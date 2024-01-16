import reversion

from datahub.company.models.export import CompanyExport
from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_limited_string, parse_uuid


class Command(CSVBaseCommand):
    """Command to update export project owner."""

    def _process_row(self, row, simulate=False, **options):
        """Process one single row."""
        pk = parse_uuid(row['export_project_id'])
        company_export = CompanyExport.objects.get(pk=pk)
        old_adviser = parse_limited_string(row['old_adviser_id'])
        new_adviser = parse_limited_string(row['new_adviser_id'])

        if company_export.owner != old_adviser:
            return

        company_export.owner = new_adviser

        if simulate:
            return

        with reversion.create_revision():
            company_export.save(update_fields=('owner',))
            reversion.set_comment('Company export owner updated.')
