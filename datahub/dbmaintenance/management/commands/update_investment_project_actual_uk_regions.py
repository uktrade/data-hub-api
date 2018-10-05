from logging import getLogger

import reversion

from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_uuid, parse_uuid_list
from datahub.investment.models import InvestmentProject


logger = getLogger(__name__)


class Command(CSVBaseCommand):
    """Command to update InvestmentProject.actual_uk_regions."""

    def _process_row(self, row, simulate=False, **options):
        """Process one single row."""
        pk = parse_uuid(row['id'])
        investment_project = InvestmentProject.objects.get(pk=pk)
        new_actual_uk_regions = parse_uuid_list(row['actual_uk_regions'])

        if investment_project.actual_uk_regions.all():
            logger.warning(
                'Not updating project with existing actual UK regions: %s, %s',
                investment_project.project_code, investment_project,
            )
            return

        if not simulate:
            with reversion.create_revision():
                investment_project.actual_uk_regions.set(new_actual_uk_regions)
                reversion.set_comment('Actual UK regions migration.')
