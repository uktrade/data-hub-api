from logging import getLogger

import reversion
from dateutil.parser import parse, parserinfo

from datahub.company.models import Company
from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_uuid

logger = getLogger(__name__)


class Command(CSVBaseCommand):
    """Command to set Company.created_on where missing.

    Some Company records have missing created_on values which
    besides being inconsistent with the parent BaseModel
    class is also causing these Companies to be omitted
    from Data Workspace.
    """

    _uk_date_format_parserinfo = parserinfo(dayfirst=True)

    def _process_row(self, row, simulate=False, **options):
        """Process a single row."""
        # .parse() creates a datetime object even in the absence of hours, minutes
        supplied_datetime = parse(
            row['Suggested Created Date'],
            parserinfo=self._uk_date_format_parserinfo,
        )

        pk = parse_uuid(row['UUID'])
        company = Company.objects.get(pk=pk)

        if company.created_on is not None:
            logger.warning(
                f'Company {pk} already has a `created_on`; skipping',
            )
            return

        if simulate:
            return

        company.created_on = supplied_datetime
        with reversion.create_revision():
            company.save(update_fields=('created_on',))
            reversion.set_comment('Created datetime updated.')
