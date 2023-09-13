import reversion

from datahub.company.models import Contact
from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_uuid


def parse_boolean(flag):
    return flag.lower() == 'true'


class Command(CSVBaseCommand):
    """Command to update the valid_email for contacts."""

    def _process_row(self, row, simulate=False, **options):
        """Process one single row."""
        pk = parse_uuid(row['id'])
        valid_email = parse_boolean(row['valid_email'])
        contact = Contact.objects.get(pk=pk)

        if contact.valid_email == valid_email:
            return

        contact.valid_email = valid_email

        if simulate:
            return

        with reversion.create_revision():
            contact.save(update_fields=('valid_email',))
            reversion.set_comment('Loaded valid_email from spreadsheet.')
