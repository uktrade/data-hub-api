from logging import getLogger

import reversion

from datahub.company.models import Contact
from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_bool, parse_uuid


logger = getLogger(__name__)


class Command(CSVBaseCommand):
    """Command to update Contact.accepts_dit_email_marketing."""

    def _process_row(self, row, simulate=False, **options):
        """Process one single row."""
        contact = Contact.objects.get(pk=parse_uuid(row['id']))
        new_accepts_dit_email_marketing = parse_bool(row['accepts_dit_email_marketing'])

        if contact.accepts_dit_email_marketing == new_accepts_dit_email_marketing:
            return

        contact.accepts_dit_email_marketing = new_accepts_dit_email_marketing

        if not simulate:
            with reversion.create_revision():
                contact.save(update_fields=('accepts_dit_email_marketing',))
                reversion.set_comment('Accepts DIT email marketing correction.')
