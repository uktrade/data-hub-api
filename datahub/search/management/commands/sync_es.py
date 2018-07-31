from logging import getLogger, WARNING

from django.core.management.base import BaseCommand, CommandError

from datahub.search.bulk_sync import sync_app
from ...apps import are_apps_initialised, get_search_apps, get_search_apps_by_name

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

        apps = get_search_apps_by_name(options['model'])

        if not are_apps_initialised(apps):
            raise CommandError(
                f'Index and mapping not initialised, please run `init_es` first.'
            )

        sync_es(
            batch_size=options['batch_size'],
            search_apps=apps
        )
