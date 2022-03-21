from logging import getLogger

from django.core.management.base import BaseCommand

from datahub.company.models.contact import Contact

logger = getLogger(__name__)


class Command(BaseCommand):
    """Command to delete investment projects."""

    def handle(self, *args, **options):
        """Populate full telephone number data."""
        logger.info('Populating full_telephone_number field...')

        for contact in Contact.objects.all().iterator(chunk_size=2000):
            contact.full_telephone_number = contact.get_full_telephone_number()
            contact.save()

        logger.info('Finished populating full_telephone_number')
