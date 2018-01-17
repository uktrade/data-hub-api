from logging import getLogger

import reversion
from rest_framework.fields import UUIDField

from datahub.investment.models import InvestmentProject
from ..base import CSVBaseCommand


logger = getLogger(__name__)


class Command(CSVBaseCommand):
    """Command to update InvestmentProject.actual_uk_regions."""

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
        pk = _parse_uuid(row['id'])
        investment_project = InvestmentProject.objects.get(pk=pk)
        new_actual_uk_regions = _parse_uuid_list(row['actual_uk_regions'])

        if investment_project.actual_uk_regions.all():
            logger.warning('Not updating project with existing actual UK regions: %s, %s',
                           investment_project.project_code, investment_project)
            return

        if not simulate:
            with reversion.create_revision():
                investment_project.actual_uk_regions.set(new_actual_uk_regions)
                reversion.set_comment('Actual UK regions migration.')


def _parse_uuid_list(value):
    if not value or value.lower().strip() == 'null':
        return []

    field = UUIDField()

    return [field.to_internal_value(item) for item in value.split(',')]


def _parse_uuid(value):
    if not value or value.lower().strip() == 'null':
        return None

    field = UUIDField()
    return field.to_internal_value(value)
