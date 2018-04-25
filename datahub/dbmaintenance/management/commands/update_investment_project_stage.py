from functools import lru_cache

import reversion

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
            dest='simulate',
            default=False,
            help='If True it only simulates the command without saving the changes.',
        )

    @lru_cache(maxsize=None)
    def get_stage(self, stage_id):
        """
        :param company_id: uuid of the company
        :return: instance of Company with id == company_id if it exists,
            None otherwise
        """
        if not stage_id or stage_id.lower().strip() == 'null':
            return None
        return InvestmentProjectStage.objects.get(id=stage_id)

    def _process_row(self, row, simulate=False, **options):
        """Process one single row."""
        investment_project = InvestmentProject.objects.get(pk=row['id'])

        new_stage = self.get_stage(row['new_stage'])

        investment_project.stage = new_stage
        if not simulate:
            with reversion.create_revision():
                investment_project.save(
                    update_fields=(
                        'stage',
                    )
                )
                reversion.set_comment('Stage migration.')
