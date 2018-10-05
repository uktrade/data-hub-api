from functools import lru_cache

from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.metadata.models import UKRegion
from datahub.omis.order.models import Order


class Command(CSVBaseCommand):
    """Command to update order.uk_region."""

    @lru_cache(maxsize=None)
    def get_region(self, uk_region_id):
        """
        :returns: instance of UKRegion with id == `uk_region_id` if it exists,
            None otherwise.
        """
        if not uk_region_id or uk_region_id.lower().strip() == 'null':
            return None
        return UKRegion.objects.get(id=uk_region_id)

    def _process_row(self, row, simulate=False, **options):
        """Process one single row."""
        order = Order.objects.get(pk=row['order_id'])
        uk_region = self.get_region(row['uk_region_id'])

        if order.uk_region != uk_region:
            order.uk_region = uk_region

            if not simulate:
                order.save(update_fields=('uk_region',))
