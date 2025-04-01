import reversion
from django.core.management.base import CommandError

from datahub.company.models import Company
from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_uuid
from datahub.export_win.models import Win


class Command(CSVBaseCommand):
    """Command to update legacy Export Win mapping to Data Hub Company."""

    def _process_row(self, row, simulate=False, **options):
        """Process one single row."""
        export_win_id = parse_uuid(row['export_win_id'])
        company_id = parse_uuid(row['data_hub_id']) if row['data_hub_id'] else None

        if company_id:
            try:
                Company.objects.get(pk=company_id)
            except Company.DoesNotExist:
                raise CommandError(f'Company with ID {company_id} does not exist')

            export_win = Win.objects.get(id=export_win_id)

            if export_win.company_id == company_id:
                return

            if not simulate:
                # The win likely will not have its original revision in the History
                with reversion.create_revision():
                    reversion.add_to_revision(export_win)
                    reversion.set_comment('Legacy export wins company migration - before.')

            export_win.company_id = company_id

            if not simulate:
                with reversion.create_revision():
                    export_win.save(
                        update_fields=('company_id',),
                    )
                    reversion.set_comment('Legacy export wins company migration - after.')
