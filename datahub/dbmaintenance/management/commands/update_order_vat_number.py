import reversion

from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_limited_string, parse_uuid
from datahub.omis.order.models import Order


class Command(CSVBaseCommand):
    """Command to update Order VAT number."""

    def _process_row(self, row, simulate=False, **options):
        """Process one single row."""
        pk = parse_uuid(row['id'])
        order = Order.objects.get(pk=pk)
        new_vat_number = parse_limited_string(row['new_vat_number'])

        order.vat_number = new_vat_number

        if simulate:
            return

        with reversion.create_revision():
            order.save(update_fields=('vat_number',))
            reversion.set_comment('Order VAT Number updated.')
