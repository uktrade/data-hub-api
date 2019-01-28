from logging import getLogger

from django.core.management.base import BaseCommand


logger = getLogger(__name__)


class Command(BaseCommand):
    """
    Usage:
        ./manage.py import_from_activity_stream
    """

    def handle(self, *args, **options):
        """Placeholder for function that has more behaviour"""
        logger.info('Started')
        logger.info('Finished')
