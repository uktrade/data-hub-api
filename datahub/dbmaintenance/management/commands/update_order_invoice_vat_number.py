import reversion

from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_limited_string, parse_uuid
from datahub.omis.invoice.models import Invoice


class Command(CSVBaseCommand):
    """Command to update Order invoice VAT number."""

    def _process_row(self, row, simulate=False, **options):
        """Process one single row."""
        pk = parse_uuid(row['id'])
        invoice = Invoice.objects.get(pk=pk)
        new_vat_number = parse_limited_string(row['new_vat_number'])

        invoice.invoice_vat_number = new_vat_number
        invoice.vat_number = new_vat_number

        if simulate:
            return

        with reversion.create_revision():
            invoice.save(update_fields=('invoice_vat_number', 'vat_number'))
            reversion.set_comment('Invoice VAT Number updated.')
