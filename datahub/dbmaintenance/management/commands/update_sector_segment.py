from logging import getLogger

import reversion

from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_limited_string, parse_uuid
from datahub.metadata.models import Sector

logger = getLogger(__name__)


class Command(CSVBaseCommand):
    """Command to update Sector.segment."""

    def _process_row(self, row, simulate=False, **options):
        """Process one single row."""
        pk = parse_uuid(row['id'])
        sector = Sector.objects.get(pk=pk)
        old_sector_segment = parse_limited_string(row['old_sector_segment'])
        new_sector_segment = parse_limited_string(row['new_sector_segment'])

        if any([sector.segment != old_sector_segment, sector.segment == new_sector_segment]):
            logger.warning(f'Not updating sector {sector} as its segment has not changed')
            return

        sector.segment = new_sector_segment

        if simulate:
            return

        with reversion.create_revision():
            sector.save(update_fields=('segment',))
            reversion.set_comment('Sector segment correction.')
