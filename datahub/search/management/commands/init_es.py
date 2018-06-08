from logging import getLogger

from django.core.management.base import BaseCommand
from django_pglocks import advisory_lock

from datahub.search.apps import get_search_apps, get_search_apps_by_name

logger = getLogger(__name__)


class Command(BaseCommand):
    """Command for creating the index and updating the mapping."""

    help = "Creates the Elasticsearch index (if necessary) and updates the index's mapping."

    def add_arguments(self, parser):
        """Handle arguments."""
        parser.add_argument(
            '--model',
            action='append',
            choices=[search_app.name for search_app in get_search_apps()],
            help='Search apps to initialise. If empty, all are initialised.',
        )

    def handle(self, *args, **options):
        """Executes the command."""
        with advisory_lock('leeloo_init_es'):
            logger.info('Creating Elasticsearch indices and initialising mappings...')

            for app in get_search_apps_by_name(options['model']):
                app.init_es()

            logger.info('Elasticsearch indices and mappings initialised')
