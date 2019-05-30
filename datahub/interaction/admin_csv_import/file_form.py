import csv
import hashlib
import io
from codecs import BOM_UTF8
from secrets import token_urlsafe

import reversion
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.defaultfilters import filesizeformat

from datahub.company.contact_matching import ContactMatchingStatus
from datahub.core.admin_csv_import import BaseCSVImportForm
from datahub.core.exceptions import DataHubException
from datahub.interaction.admin_csv_import.cache_utils import (
    load_file_contents_and_name,
    save_file_contents_and_name,
)
from datahub.interaction.admin_csv_import.duplicate_checking import DuplicateTracker
from datahub.interaction.admin_csv_import.row_form import InteractionCSVRowForm


REVISION_COMMENT = 'Imported from file via the admin site.'


class UnmatchedRowCollector:
    """Holds unmatched rows following an import operation."""

    def __init__(self):
        """Initialise the instance with an empty list of rows."""
        self.rows = []

    def append_row(self, row_form):
        """Add an unmatched row."""
        self.rows.append(row_form.data)

    def to_raw_csv(self):
        """
        Generate a CSV file from collected unmatched rows.

        The CSV file is in the same format as the input file (so that it can be re-uploaded
        at a later date if required).
        """
        if not self.rows:
            return None

        byte_stream = io.BytesIO()
        byte_stream.write(BOM_UTF8)

        with byte_stream:
            text_stream = io.TextIOWrapper(byte_stream, encoding='utf-8', write_through=True)
            # Use the keys of the first row for the fieldnames argument (all rows should have
            # the same keys)
            writer = csv.DictWriter(text_stream, self.rows[0].keys())
            writer.writeheader()
            writer.writerows(self.rows)
            return byte_stream.getvalue()


class InteractionCSVForm(BaseCSVImportForm):
    """Form used for loading a CSV file to import interactions."""

    csv_file_field_label = 'Interaction list (CSV file)'
    csv_file_field_help_text = (
        f'Maximum file size: {filesizeformat(settings.INTERACTION_ADMIN_CSV_IMPORT_MAX_SIZE)}'
    )
    required_columns = InteractionCSVRowForm.get_required_field_names()

    def are_all_rows_valid(self):
        """Check if all of the rows in the CSV pass validation."""
        return all(row_form.is_valid() for row_form in self._get_row_form_iterator())

    def get_row_error_iterator(self):
        """Get a generator of CSVRowError instances."""
        for row_form in self._get_row_form_iterator():
            yield from row_form.get_flat_error_list_iterator()

    def get_matching_summary(self, max_rows):
        """
        Get a summary of the contact matching results of the rows.

        This is used as part of the preview page displayed once a file has been uploaded.

        :returns: dict of counts by `ContactMatchingStatus` and list of matched rows as
            serializer dicts
        """
        matching_counts = {status: 0 for status in ContactMatchingStatus}
        matched_rows = []

        for row_form in self._get_row_form_iterator(raise_error_if_invalid=True):
            contact_matching_status = row_form.cleaned_data['contact_matching_status']
            matching_counts[contact_matching_status] += 1

            is_row_matched = contact_matching_status == ContactMatchingStatus.matched

            if is_row_matched and len(matched_rows) < max_rows:
                matched_rows.append(row_form.cleaned_data_as_serializer_dict())

        return matching_counts, matched_rows

    @reversion.create_revision()
    def save(self, user):
        """Saves all loaded rows matched with contacts."""
        reversion.set_comment(REVISION_COMMENT)

        csv_file = self.cleaned_data['csv_file']
        sha256 = _sha256_for_file(csv_file)

        source = {
            'file': {
                'name': csv_file.name,
                'size': csv_file.size,
                'sha256': sha256.hexdigest(),
            },
        }

        matching_counts = {status: 0 for status in ContactMatchingStatus}
        unmatched_row_collector = UnmatchedRowCollector()

        for row_form in self._get_row_form_iterator(raise_error_if_invalid=True):
            if row_form.is_matched():
                row_form.save(user, source)
            else:
                unmatched_row_collector.append_row(row_form)

            matching_counts[row_form.cleaned_data['contact_matching_status']] += 1

        return matching_counts, unmatched_row_collector

    def save_to_cache(self):
        """
        Generate a token and store the file in the configured cache with a timeout.

        Can only be called on a validated form.
        """
        token = token_urlsafe()

        csv_file = self.cleaned_data['csv_file']
        csv_file.seek(0)
        contents = csv_file.read()

        save_file_contents_and_name(token, contents, csv_file.name)
        return token

    @classmethod
    def from_token(cls, token):
        """
        Create a InteractionCSVForm instance using a token.

        Returns None if serialised data for the token can't be found in the cache.
        """
        file_contents_and_name = load_file_contents_and_name(token)
        if not file_contents_and_name:
            return None

        contents, name = file_contents_and_name
        csv_file = SimpleUploadedFile(name=name, content=contents)

        return cls(
            files={
                'csv_file': csv_file,
            },
        )

    def _get_row_form_iterator(self, raise_error_if_invalid=False):
        """
        Get a generator over InteractionCSVRowForm instances.

        This should only be called if the rows have previously been validated.
        """
        duplicate_tracker = DuplicateTracker()

        with self.open_file_as_dict_reader() as dict_reader:
            for index, row in enumerate(dict_reader):
                row_form = InteractionCSVRowForm(
                    row_index=index,
                    data=row,
                    duplicate_tracker=duplicate_tracker,
                )

                if not row_form.is_valid() and raise_error_if_invalid:
                    # We are not expecting this to happen. Raise an exception to alert us if
                    # it does.
                    raise DataHubException('CSV row unexpectedly failed revalidation')

                yield row_form


def _sha256_for_file(file):
    file.seek(0)

    sha256 = hashlib.sha256()
    for line in file:
        sha256.update(line)

    return sha256
