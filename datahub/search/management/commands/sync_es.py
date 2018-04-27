from logging import getLogger, WARNING

from django.core.management.base import BaseCommand

from datahub.search.bulk_sync import DEFAULT_BATCH_SIZE, get_datasets, sync_dataset
from ...apps import get_search_apps

logger = getLogger(__name__)


def sync_es(batch_size, datasets):
    """Sends data to Elasticsearch."""
    for item in datasets:
        sync_dataset(item, batch_size=batch_size)

    logger.info('Elasticsearch sync complete!')


class Command(BaseCommand):
    """Elasticsearch sync command."""

    def add_arguments(self, parser):
        """Handle arguments."""
        parser.add_argument(
            '--batch_size',
            dest='batch_size',
            default=DEFAULT_BATCH_SIZE,
            help='Batch size - number of rows processed at a time',
        )
        parser.add_argument(
            '--model',
            dest='model',
            action='append',
            choices=[search_app.name for search_app in get_search_apps()],
            help='Search model to import. If empty, it imports all',
        )

    def handle(self, *args, **options):
        """Handle."""
        es_logger = getLogger('elasticsearch')
        es_logger.setLevel(WARNING)

        sync_es(
            batch_size=options['batch_size'],
            datasets=get_datasets(options['model'])
        )
