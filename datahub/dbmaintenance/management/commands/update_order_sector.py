from logging import getLogger

import reversion

from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_uuid
from datahub.metadata.models import Sector
from datahub.omis.order.models import Order


logger = getLogger(__name__)


class Command(CSVBaseCommand):
    """Command to update Order.sector."""

    def _process_row(self, row, simulate=False, overwrite=False, **options):
        """Process a single row."""
        pk = parse_uuid(row['id'])
        order = Order.objects.get(pk=pk)
        old_sector_id = parse_uuid(row['old_sector_id'])
        new_sector_id = parse_uuid(row['new_sector_id'])

        if any([order.sector.pk != old_sector_id, order.sector.pk == new_sector_id]):
            logger.warning(
                f'Not updating order {order} as its sector has not changed',
            )
            return

        order.sector = Sector.objects.get(pk=new_sector_id)

        if simulate:
            return

        with reversion.create_revision():
            order.save(update_fields=('sector',))
            reversion.set_comment('Order sector correction.')
