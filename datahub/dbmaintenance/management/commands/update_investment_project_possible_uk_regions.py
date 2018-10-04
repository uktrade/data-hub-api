from logging import getLogger

import reversion

from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_bool, parse_uuid, parse_uuid_list
from datahub.investment.models import InvestmentProject


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
            '--ignore-old-regions',
            action='store_true',
            default=False,
            help='If True it does not check if the regions match the old_uk_region_locations '
                 'column.',
        )

    def _process_row(self, row, simulate=False, ignore_old_regions=False, **options):
        """Process one single row."""
        pk = parse_uuid(row['id'])
        investment_project = InvestmentProject.objects.get(pk=pk)
        allow_blank_possible_uk_regions = parse_bool(row['allow_blank_possible_uk_regions'])
        uk_region_locations = parse_uuid_list(row['uk_region_locations'])

        current_regions = investment_project.uk_region_locations.all()
        current_region_ids = set(region.pk for region in current_regions)
        if (investment_project.allow_blank_possible_uk_regions == allow_blank_possible_uk_regions
                and current_region_ids == set(uk_region_locations)):
            return

        if not ignore_old_regions:
            old_uk_region_locations = parse_uuid_list(row['old_uk_region_locations'])

            if current_region_ids != set(old_uk_region_locations):
                return

        investment_project.allow_blank_possible_uk_regions = allow_blank_possible_uk_regions

        if simulate:
            return

        with reversion.create_revision():
            investment_project.save(
                update_fields=('allow_blank_possible_uk_regions',),
            )
            investment_project.uk_region_locations.set(uk_region_locations)
            reversion.set_comment('Possible UK regions data migration correction.')
