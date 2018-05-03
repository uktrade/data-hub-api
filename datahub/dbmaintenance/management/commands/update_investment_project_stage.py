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
            '--simulate',
            action='store_true',
            default=False,
            help='If True it only simulates the command without saving the changes.',
        )
        parser.add_argument(
            '--adviser',
            help='UUID of a valid adviser to use as the modified_by value',
        )

    @lru_cache(maxsize=None)
    def get_stage(self, stage_id):
        """
        :param stage_id: uuid of the Investment project stage
        :return: instance of investment project stage with id == stage_id if it exists,
            None otherwise
        """
        if not stage_id or stage_id == 'null':
            return None
        return InvestmentProjectStage.objects.get(id=stage_id)

    def get_adviser(self, adviser_id):
        """
        :param adviser: uuid of an adviser
        :return: instance of an adviser if they exist,
            None otherwise
        """
        if not adviser_id or adviser_id == 'null':
            return None
        return Advisor.objects.get(id=adviser_id)

    def _process_row(self, row, simulate=False, adviser=False, **options):
        """Process one single row."""
        investment_project_id = parse_uuid(row['investment_project_id'])
        stage_id = parse_uuid(row['stage_id'])
        adviser_id = parse_uuid(adviser)

        investment_project = InvestmentProject.objects.get(pk=investment_project_id)

        new_stage = self.get_stage(stage_id)
        current_adviser = self.get_adviser(adviser_id) or investment_project.modified_by
        investment_project.stage = new_stage

        if current_adviser:
            investment_project.modified_by = current_adviser

        if not simulate:
            with reversion.create_revision():
                investment_project.save(
                    update_fields=(
                        'stage',
                        'modified_by'
                    )
                )
                reversion.set_comment('Stage correction.')
