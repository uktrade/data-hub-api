from logging import getLogger

import reversion

from datahub.company.models import Company
from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_uuid


logger = getLogger(__name__)


class Command(CSVBaseCommand):
    """Command to update Company.uk_region."""

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
        uk_region_id = parse_uuid(row['uk_region_id'])

        if company.uk_region_id and not overwrite:
            logger.warning(
                f'Skipping update of company {company.pk} as it already has a UK region.',
            )
            return

        if company.uk_region_id == uk_region_id:
            return

        company.uk_region_id = uk_region_id

        if simulate:
            return

        with reversion.create_revision():
            company.save(update_fields=('uk_region_id',))
            reversion.set_comment('UK region updated.')
