from logging import getLogger

import reversion

from datahub.company.models import Company
from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_limited_string, parse_uuid


logger = getLogger(__name__)


class Command(CSVBaseCommand):
    """Command to update Company.duns_number."""

    def _process_row(self, row, simulate=False, **options):
        """Process one single row."""
        pk = parse_uuid(row['id'])
        company = Company.objects.get(pk=pk)
        duns_number = parse_limited_string(row['duns_number'], blank_value=None)

        if company.duns_number == duns_number:
            return

        company.duns_number = duns_number

        if simulate:
            return

        with reversion.create_revision():
            company.save(update_fields=('duns_number',))
            reversion.set_comment('Duns number updated.')
