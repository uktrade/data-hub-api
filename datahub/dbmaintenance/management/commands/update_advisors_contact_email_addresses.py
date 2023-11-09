import reversion

from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_email, parse_uuid
from datahub.company.models import Contact


class Command(CSVBaseCommand):
    """Command to update the email for contacts that have with @trade in it."""

    def _process_row(self, row, simulate=False, **options):
        """Process one row"""
        pk = parse_uuid(row['Adviser ID'])
        email = parse_email(row['New Contact email'])
        contact = Contact.objects.get(pk=pk)

        if '@trade' not in contact.email:
            return

        contact.email = email

        if simulate:
            return

        with reversion.create_revision():
            contact.save(update_fields=('email',))
            reversion.set_comment('Loaded email from spreadsheet.')
