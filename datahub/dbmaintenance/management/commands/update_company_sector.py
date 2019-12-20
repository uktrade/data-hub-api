from logging import getLogger

import reversion

from datahub.company.models import Company
from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_uuid


logger = getLogger(__name__)


class Command(CSVBaseCommand):
    """Command to update Company.sector."""

    def add_arguments(self, parser):
        """Define additional arguments."""
        super().add_arguments(parser)

        parser.add_argument(
            '--overwrite',
            action='store_true',
            default=False,
            help='Overwrite existing values rather than leaving them in place.',
        )

    def _process_row(self, row, simulate=False, overwrite=False, **options):
        """Process a single row."""
        pk = parse_uuid(row['id'])
        company = Company.objects.get(pk=pk)
        sector_id = parse_uuid(row['sector_id'])

        if company.sector_id and not overwrite:
            logger.warning(
                f'Skipping update of company {company.pk} as it already has a sector.',
            )
            return

        if company.sector_id == sector_id:
            return

        company.sector_id = sector_id

        if simulate:
            return

        with reversion.create_revision():
            company.save(update_fields=('sector_id',))
            reversion.set_comment('Sector updated.')
