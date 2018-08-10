from logging import getLogger

import reversion

from datahub.company.models import Contact
from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_bool, parse_uuid
from datahub.search.signals import disable_search_signal_receivers

logger = getLogger(__name__)


class Command(CSVBaseCommand):
    """Command to update Contact.accepts_dit_email_marketing."""

    @disable_search_signal_receivers(Contact)
    def _handle(self, *args, **options):
        """
        Disables search signal receivers for contacts.

        This is to avoid generating huge numbers of sync thread-pool tasks for those contacts
        and their interactions.

        (Syncing can be manually performed afterwards using sync_es if required.)
        """
        return super()._handle(*args, **options)

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
