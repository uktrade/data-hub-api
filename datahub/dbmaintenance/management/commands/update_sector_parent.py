from logging import getLogger

import reversion

from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_uuid
from datahub.metadata.models import Sector


logger = getLogger(__name__)


class Command(CSVBaseCommand):
    """Command to update Sector.parent."""

    def _process_row(self, row, simulate=False, **options):
        """Process one single row."""
        pk = parse_uuid(row['id'])
        sector = Sector.objects.get(pk=pk)
        old_parent_pk = parse_uuid(row['old_parent_id'])
        new_parent_pk = parse_uuid(row['new_parent_id'])

        if sector.parent and any(
            [sector.parent.pk != old_parent_pk, sector.parent.pk == new_parent_pk],
        ):
            logger.warning(f'Not updating sector {sector} as its parent has not changed')
            return

        if new_parent_pk:
            new_parent = Sector.objects.get(pk=new_parent_pk)
        else:
            new_parent = None

        if simulate:
            return

        with reversion.create_revision():
            sector.move_to(new_parent)
            reversion.set_comment('Sector parent correction.')
