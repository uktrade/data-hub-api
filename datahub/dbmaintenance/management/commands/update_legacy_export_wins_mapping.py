from django.core.management.base import CommandError
from django.db import transaction

from datahub.company.models import Company
from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_uuid
from datahub.export_win.models import LegacyExportWinsToDataHubCompany


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

        with transaction.atomic():
            mapping, created = LegacyExportWinsToDataHubCompany.objects.get_or_create(
                id=export_win_id,
                defaults={
                    'company_id': company_id,
                },
            )
            if not created:
                mapping.company_id = company_id
                mapping.save()

            if simulate:
                transaction.set_rollback(True)
