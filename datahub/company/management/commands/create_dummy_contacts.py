from logging import getLogger

from django.core.management.base import BaseCommand

from datahub.company.test.factories import ContactFactory

logger = getLogger(__name__)


class Command(BaseCommand):
    """Command to delete investment projects."""

    def handle(self, *args, **options):
        """Populate full telephone number data."""
        logger.info('Adding dummy contacts...')

        for _ in range(20000):
            ContactFactory().save()

        logger.info('Finished adding dummy contacts')
