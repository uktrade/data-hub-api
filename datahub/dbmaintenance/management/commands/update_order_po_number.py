import reversion

from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_limited_string, parse_uuid
from datahub.omis.order.models import Order


class Command(CSVBaseCommand):
    """Command to update Order PO number."""

    def _process_row(self, row, simulate=False, **options):
        """Process one single row."""
        pk = parse_uuid(row['id'])
        order = Order.objects.get(pk=pk)
        new_po_number = parse_limited_string(row['new_po_number'])

        order.po_number = new_po_number

        if simulate:
            return

        with reversion.create_revision():
            order.save(update_fields=('po_number',))
            reversion.set_comment('Order PO number updated.')
