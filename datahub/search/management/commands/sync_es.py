from logging import getLogger, WARNING

from django.core.management.base import BaseCommand, CommandError

from datahub.search.apps import are_apps_initialised, get_search_apps, get_search_apps_by_name
from datahub.search.tasks import sync_model

logger = getLogger(__name__)


class Command(BaseCommand):
    """Elasticsearch sync command."""

    def add_arguments(self, parser):
        """Handle arguments."""
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
                f'Index and mapping not initialised, please run `init_es` first.',
            )

        for app in apps:
            sync_model.apply(args=(app.name,), throw=True)

        logger.info('Elasticsearch sync complete!')
