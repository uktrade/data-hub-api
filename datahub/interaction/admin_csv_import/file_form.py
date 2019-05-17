import gzip
import hashlib
from datetime import timedelta
from secrets import token_urlsafe

import reversion
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.defaultfilters import filesizeformat

from datahub.company.contact_matching import ContactMatchingStatus
from datahub.core.admin_csv_import import BaseCSVImportForm
from datahub.core.exceptions import DataHubException
from datahub.interaction.admin_csv_import.row_form import InteractionCSVRowForm


FILE_CACHE_TIMEOUT_SECS = int(timedelta(minutes=30).total_seconds())
REVISION_COMMENT = 'Imported from file via the admin site.'


class InteractionCSVForm(BaseCSVImportForm):
    """Form used for loading a CSV file to import interactions."""

    csv_file_field_label = 'Interaction list (CSV file)'
    csv_file_field_help_text = (
        f'Maximum file size: {filesizeformat(settings.INTERACTION_ADMIN_CSV_IMPORT_MAX_SIZE)}'
    )
    required_columns = InteractionCSVRowForm.get_required_field_names()

    def are_all_rows_valid(self):
        """Check if all of the rows in the CSV pass validation."""
        with self.open_file_as_dict_reader() as dict_reader:
            return all(InteractionCSVRowForm(data=row).is_valid() for row in dict_reader)

    def get_row_error_iterator(self):
        """Get a generator of CSVRowError instances."""
        with self.open_file_as_dict_reader() as dict_reader:
            for index, row in enumerate(dict_reader):
                form = InteractionCSVRowForm(row_index=index, data=row)
                yield from form.get_flat_error_list_iterator()

    def get_matching_summary(self, max_rows):
        """
        Get a summary of the contact matching results of the rows.

        This is used as part of the preview page displayed once a file has been uploaded.

        :returns: dict of counts by `ContactMatchingStatus` and list of matched rows as
            serializer dicts
        """
        matching_counts = {status: 0 for status in ContactMatchingStatus}
        matched_rows = []

        for row_form in self._get_validated_row_form_iterator():
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

        for row_form in self._get_validated_row_form_iterator():
            if row_form.is_matched():
                row_form.save(user, source)

            matching_counts[row_form.cleaned_data['contact_matching_status']] += 1

        return matching_counts

    def save_to_cache(self):
        """
        Generate a token and store the file in the configured cache with a timeout.

        Can only be called on a validated form.
        """
        csv_file = self.cleaned_data['csv_file']
        csv_file.seek(0)
        data = csv_file.read()
        compressed_data = gzip.compress(data)

        token = _make_token()
        data_key, name_key = _cache_keys_for_token(token)
        cache_keys_and_values = {
            data_key: compressed_data,
            name_key: csv_file.name,
        }
        cache.set_many(cache_keys_and_values, timeout=FILE_CACHE_TIMEOUT_SECS)
        return token

    @classmethod
    def from_token(cls, token):
        """
        Create a InteractionCSVForm instance using a token.

        Returns None if serialised data for the token can't be found in the cache.
        """
        data_key, name_key = _cache_keys_for_token(token)
        cache_keys_and_values = cache.get_many((data_key, name_key))

        any_cache_keys_missing = {data_key, name_key} - cache_keys_and_values.keys()
        if any_cache_keys_missing:
            return None

        decompressed_data = gzip.decompress(cache_keys_and_values[data_key])
        name = cache_keys_and_values[name_key]
        csv_file = SimpleUploadedFile(name=name, content=decompressed_data)

        return cls(
            files={
                'csv_file': csv_file,
            },
        )

    def _get_validated_row_form_iterator(self):
        """
        Get a generator over InteractionCSVRowForm instances.

        This should only be called if the rows have previously been validated.
        """
        with self.open_file_as_dict_reader() as dict_reader:
            for index, row in enumerate(dict_reader):
                row_form = InteractionCSVRowForm(row_index=index, data=row)

                if not row_form.is_valid():
                    # We are not expecting this to happen. Raise an exception to alert us if
                    # it does.
                    raise DataHubException('CSV row unexpectedly failed revalidation')

                yield row_form


def _make_token():
    return token_urlsafe()


def _cache_keys_for_token(token):
    prefix = f'interaction-csv-import:{token}'
    return f'{prefix}:data', f'{prefix}:name'


def _sha256_for_file(file):
    file.seek(0)

    sha256 = hashlib.sha256()
    for line in file:
        sha256.update(line)

    return sha256
