from logging import getLogger
from uuid import UUID

import reversion

from datahub.core.constants import InvestmentProjectStage
from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_date
from datahub.investment.models import InvestmentProject


logger = getLogger(__name__)


class Command(CSVBaseCommand):
    """
    Command to update investment_project.actual_land_date.

    Any projects in the Won stage are not updated.
    """

    def _process_row(self, row, simulate=False, **options):
        """Process one single row."""
        investment_project = InvestmentProject.objects.get(pk=row['id'])
        old_actual_land_date = parse_date(row['old_actual_land_date'])
        new_actual_land_date = parse_date(row['new_actual_land_date'])

        if investment_project.actual_land_date != old_actual_land_date:
            return

        if investment_project.actual_land_date == new_actual_land_date:
            return

        if investment_project.stage_id == UUID(InvestmentProjectStage.won.value.id):
            logger.warning(
                'Not updating project in Won stage: %s, %s',
                investment_project.project_code, investment_project,
            )
            return

        investment_project.actual_land_date = new_actual_land_date

        if not simulate:
            with reversion.create_revision():
                investment_project.save(update_fields=('actual_land_date',))
                reversion.set_comment('Actual land date migration correction.')
