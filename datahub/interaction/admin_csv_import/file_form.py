import gzip
from datetime import timedelta
from secrets import token_urlsafe

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.defaultfilters import filesizeformat

from datahub.company.contact_matching import ContactMatchingStatus
from datahub.core.admin_csv_import import BaseCSVImportForm
from datahub.core.exceptions import DataHubException
from datahub.interaction.admin_csv_import.row_form import InteractionCSVRowForm


FILE_CACHE_TIMEOUT_SECS = int(timedelta(minutes=30).total_seconds())


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

        with self.open_file_as_dict_reader() as dict_reader:
            for index, row in enumerate(dict_reader):
                form = InteractionCSVRowForm(row_index=index, data=row)

                if not form.is_valid():
                    # This should not happen. Just raise an exception to alert us if it does.
                    raise DataHubException('CSV row unexpectedly failed revalidation')

                contact_matching_status = form.cleaned_data['contact_matching_status']
                matching_counts[contact_matching_status] += 1

                is_row_matched = contact_matching_status == ContactMatchingStatus.matched

                if is_row_matched and len(matched_rows) < max_rows:
                    matched_rows.append(form.cleaned_data_as_serializer_dict())

        return matching_counts, matched_rows

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


def _make_token():
    return token_urlsafe()


def _cache_keys_for_token(token):
    prefix = f'interaction-csv-import:{token}'
    return f'{prefix}:data', f'{prefix}:name'
