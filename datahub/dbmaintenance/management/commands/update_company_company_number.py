from logging import getLogger

import reversion

from datahub.company.models import Company
from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_limited_string, parse_uuid


logger = getLogger(__name__)


class Command(CSVBaseCommand):
    """Command to update Company.company_number."""

    def _process_row(self, row, simulate=False, **options):
        """Process one single row."""
        pk = parse_uuid(row['id'])
        company = Company.objects.get(pk=pk)
        company_number = parse_limited_string(row['company_number'])

        if company.company_number == company_number:
            return

        company.company_number = company_number

        if simulate:
            return

        with reversion.create_revision():
            company.save(update_fields=('company_number',))
            reversion.set_comment('Company number updated.')
