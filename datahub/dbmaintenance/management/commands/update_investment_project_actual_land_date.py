from datetime import datetime
from logging import getLogger
from uuid import UUID

import reversion

from datahub.core.constants import InvestmentProjectStage
from datahub.investment.models import InvestmentProject
from ..base import CSVBaseCommand


logger = getLogger(__name__)


class Command(CSVBaseCommand):
    """
    Command to update investment_project.actual_land_date.

    Any projects in the Won stage are not updated.
    """

    def add_arguments(self, parser):
        """Define extra arguments."""
        super().add_arguments(parser)
        parser.add_argument(
            '--simulate',
            action='store_true',
            dest='simulate',
            default=False,
            help='If True it only simulates the command without saving the changes.',
        )

    def _process_row(self, row, simulate=False, **options):
        """Process one single row."""
        investment_project = InvestmentProject.objects.get(pk=row['id'])
        old_actual_land_date = _parse_date(row['old_actual_land_date'])
        new_actual_land_date = _parse_date(row['new_actual_land_date'])

        if investment_project.actual_land_date != old_actual_land_date:
            return

        if investment_project.actual_land_date == new_actual_land_date:
            return

        if investment_project.stage_id == UUID(InvestmentProjectStage.won.value.id):
            logger.warning('Not updating project in Won stage: %s, %s',
                           investment_project.project_code, investment_project)
            return

        investment_project.actual_land_date = new_actual_land_date

        if not simulate:
            with reversion.create_revision():
                investment_project.save(update_fields=('actual_land_date',))
                reversion.set_comment('Actual land date migration correction.')


def _parse_date(date_str):
    if not date_str or date_str.lower().strip() == 'null':
        return None
    return datetime.strptime(date_str, '%Y-%m-%d').date()
