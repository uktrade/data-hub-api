from logging import getLogger

import reversion
from rest_framework.fields import BooleanField, UUIDField

from datahub.investment.models import InvestmentProject
from ..base import CSVBaseCommand


logger = getLogger(__name__)


class Command(CSVBaseCommand):
    """
    Command to update investment_project.uk_region_locations and
    investment_project.allow_blank_possible_uk_regions.
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
        pk = _parse_uuid(row['id'])
        investment_project = InvestmentProject.objects.get(pk=pk)
        allow_blank_possible_uk_regions = _parse_bool(row['allow_blank_possible_uk_regions'])
        uk_region_locations = _parse_uuid_list(row['uk_region_locations'])

        current_regions = investment_project.uk_region_locations.all()
        current_region_ids = set(region.pk for region in current_regions)
        if (investment_project.allow_blank_possible_uk_regions == allow_blank_possible_uk_regions
                and current_region_ids == set(uk_region_locations)):
            return

        investment_project.allow_blank_possible_uk_regions = allow_blank_possible_uk_regions

        if simulate:
            return

        with reversion.create_revision():
            investment_project.save(
                update_fields=('allow_blank_possible_uk_regions',)
            )
            investment_project.uk_region_locations.set(uk_region_locations)
            reversion.set_comment('Possible UK regions data migration correction.')


def _parse_bool(value):
    return _parse_value(value, BooleanField())


def _parse_uuid(value):
    return _parse_value(value, UUIDField())


def _parse_uuid_list(value):
    if not value or value.lower().strip() == 'null':
        return []

    field = UUIDField()

    return [field.to_internal_value(item) for item in value.split(',')]


def _parse_value(value, field):
    if not value or value.lower().strip() == 'null':
        return None

    return field.to_internal_value(value)
