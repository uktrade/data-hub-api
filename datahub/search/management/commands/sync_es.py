from logging import getLogger, WARNING

from django.core.management.base import BaseCommand

from datahub.search.bulk_sync import get_apps_to_sync, sync_app
from ...apps import get_search_apps

logger = getLogger(__name__)


def sync_es(batch_size, search_apps):
    """Sends data to Elasticsearch."""
    for app in search_apps:
        sync_app(app, batch_size=batch_size)

    logger.info('Elasticsearch sync complete!')


class Command(BaseCommand):
    """Elasticsearch sync command."""

    def add_arguments(self, parser):
        """Handle arguments."""
        parser.add_argument(
            '--batch_size',
            type=int,
            help='Batch size - number of rows processed at a time (defaults to per-model '
                 'defaults)',
        )
        parser.add_argument(
            '--model',
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
            search_apps=get_apps_to_sync(options['model'])
        )
