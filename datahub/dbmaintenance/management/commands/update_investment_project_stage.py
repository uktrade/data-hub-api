from datetime import datetime
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
            '--user',
            default=False,
            dest='user',
            action='store',
            help='UUID of a valid adviser to use as the modified_by value',
        )

    @lru_cache(maxsize=None)
    def get_stage(self, stage_id):
        """
        :param company_id: uuid of the company
        :return: instance of investment project stage with id == stage_id if it exists,
            None otherwise
        """
        if not stage_id or stage_id == 'null':
            return None
        return InvestmentProjectStage.objects.get(id=stage_id)

    def get_adviser(self, adviser_id):
        """
        :param adviser: uuid of the company
        :return: instance of a data hub adviser,
            None otherwise
        """
        if not adviser_id or adviser_id == 'null':
            return None
        return Advisor.objects.get(id=adviser_id)

    def _process_row(self, row, simulate=False, user=False, **options):
        """Process one single row."""
        id = parse_uuid(row['id'])
        stage = parse_uuid(row['new_stage'])
        adviser = parse_uuid(user)

        investment_project = InvestmentProject.objects.get(pk=id)

        new_stage = self.get_stage(stage)
        dh_user = self.get_adviser(adviser)
        if not dh_user:
            dh_user = investment_project.modified_by

        investment_project.stage = new_stage
        investment_project.modified_on = datetime.now()
        investment_project.modified_by = dh_user

        if not simulate:
            with reversion.create_revision():
                investment_project.save(
                    update_fields=(
                        'stage',
                        'modified_on',
                        'modified_by'
                    )
                )
                reversion.set_comment('Stage correction.')
