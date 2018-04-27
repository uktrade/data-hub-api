from logging import getLogger

from django.core.management.base import BaseCommand
from django_pglocks import advisory_lock

from datahub.search.apps import get_search_apps
from datahub.search.migrate import migrate_apps

logger = getLogger(__name__)


class Command(BaseCommand):
    """Command for migrating an Elasticsearch index."""

    help = "Creates the Elasticsearch index (if necessary) and updates the index's mapping."

    def add_arguments(self, parser):
        """Handle arguments."""
        parser.add_argument(
            '--model',
            action='append',
            choices=[search_app.name for search_app in get_search_apps()],
            help='Search apps to migrate. If empty, all are migrated.',
        )

    def handle(self, *args, **options):
        """Executes the command."""
        with advisory_lock('leeloo_migrate_es'):
            migrate_apps(app_names=options['model'])
