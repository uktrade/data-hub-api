import reversion

from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_uuid
from datahub.export_win.models import Win


class Command(CSVBaseCommand):
    """Command to update legacy Export Win data."""

    def _process_row(self, row, simulate=False, **options):
        """Process one single row."""
        export_win_id = parse_uuid(row['id'])

        export_win = Win.objects.get(id=export_win_id)
        export_win.company_name = row['company_name']
        export_win.lead_officer_name = row['lead_officer_name']
        export_win.lead_officer_email_address = row['lead_officer_email_address']
        export_win.adviser_name = row['user_name']
        export_win.adviser_email_address = row['user_email']
        export_win.line_manager_name = row['line_manager_name']
        export_win.customer_name = row['customer_name']
        export_win.customer_job_title = row['customer_job_title']
        export_win.customer_email_address = row['customer_email_address']

        if not simulate:
            with reversion.create_revision():
                export_win.save(
                    update_fields=(
                        'company_name',
                        'lead_officer_name',
                        'lead_officer_email_address',
                        'adviser_name',
                        'adviser_email_address',
                        'line_manager_name',
                        'customer_name',
                        'customer_job_title',
                        'customer_email_address',
                    ),
                )
                reversion.set_comment('Legacy export wins data migration.')
