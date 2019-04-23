from django.conf import settings
from django.template.defaultfilters import filesizeformat

from datahub.core.admin_csv_import import BaseCSVImportForm


class InteractionCSVForm(BaseCSVImportForm):
    """Form used for loading a CSV file to import interactions."""

    csv_file_field_label = 'Interaction list (CSV file)'
    csv_file_field_help_text = (
        f'Maximum file size: {filesizeformat(settings.INTERACTION_ADMIN_CSV_IMPORT_MAX_SIZE)}'
    )
    required_columns = {
        'kind',
        'date',
        'service',
        'contact_email',
        'adviser_1',
    }
