from functools import lru_cache

import reversion

from datahub.company.models import Advisor
from datahub.dbmaintenance.utils import parse_uuid
from datahub.investment.models import InvestmentProject
from datahub.metadata.models import InvestmentProjectStage
from ..base import CSVBaseCommand


class Command(CSVBaseCommand):
    """Command to update investment_project.stage."""

    def add_arguments(self, parser):
        """Define extra arguments."""
        super().add_arguments(parser)
        parser.add_argument(
            '--modified_by',
            help='UUID of a valid adviser to use as the modified_by value',
        )

    @lru_cache(maxsize=None)
    def get_stage(self, stage_id):
        """
        :param stage_id: uuid of the Investment project stage
        :return: instance of investment project stage with id == stage_id if it exists,
            None otherwise
        """
        if not stage_id:
            return None
        return InvestmentProjectStage.objects.get(id=stage_id)

    @lru_cache(maxsize=None)
    def get_adviser(self, adviser_id):
        """
        :param adviser: uuid of an adviser
        :return: instance of an adviser if they exist,
            None otherwise
        """
        if not adviser_id:
            return None
        return Advisor.objects.get(id=adviser_id)

    def _process_row(self, row, simulate=False, modified_by=None, **options):
        """Process one single row."""
        investment_project_id = parse_uuid(row['investment_project_id'])
        stage_id = parse_uuid(row['stage_id'])
        adviser_id = parse_uuid(modified_by)

        investment_project = InvestmentProject.objects.get(pk=investment_project_id)

        investment_project.stage = self.get_stage(stage_id)
        investment_project.modified_by = self.get_adviser(adviser_id)

        if not simulate:
            with reversion.create_revision():
                investment_project.save(
                    update_fields=(
                        'stage',
                        'modified_by',
                        'modified_on'
                    )
                )
                reversion.set_comment('Stage correction.')
