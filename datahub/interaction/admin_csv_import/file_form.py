from django.conf import settings
from django.template.defaultfilters import filesizeformat

from datahub.core.admin_csv_import import BaseCSVImportForm
from datahub.interaction.admin_csv_import.row_form import InteractionCSVRowForm


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
