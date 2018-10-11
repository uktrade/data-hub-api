from logging import getLogger

import reversion

from datahub.company.models import Company
from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_limited_string, parse_uuid


logger = getLogger(__name__)


class Command(CSVBaseCommand):
    """Command to update Company.alias."""

    def _process_row(self, row, simulate=False, **options):
        """Process one single row."""
        pk = parse_uuid(row['id'])
        company = Company.objects.get(pk=pk)
        old_company_alias = parse_limited_string(row['old_company_alias'])
        new_company_alias = parse_limited_string(row['new_company_alias'])

        if company.alias != old_company_alias:
            return

        company.alias = new_company_alias

        if simulate:
            return

        with reversion.create_revision():
            company.save(update_fields=('alias',))
            reversion.set_comment('Company alias correction.')
