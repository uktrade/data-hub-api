import reversion

from datahub.company.models import Contact
from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_email, parse_uuid


class Command(CSVBaseCommand):
    """Command to update the email for contacts."""

    def _process_row(self, row, simulate=False, **options):
        """Process one single row."""
        pk = parse_uuid(row['id'])
        email = parse_email(row['email'])
        contact = Contact.objects.get(pk=pk)

        if contact.email == email:
            return

        contact.email = email

        if simulate:
            return

        with reversion.create_revision():
            contact.save(update_fields=('email',))
            reversion.set_comment('Loaded email from spreadsheet.')
