from logging import getLogger

from django.core.management.base import BaseCommand, CommandError
from django_pglocks import advisory_lock

from datahub.search.apps import are_apps_initialised, get_search_apps, get_search_apps_by_name
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
        apps = get_search_apps_by_name(options['model'])

        if not are_apps_initialised(apps):
            raise CommandError(
                f'Index and mapping not initialised, please run `init_es` first.'
            )

        with advisory_lock('leeloo_migrate_es'):
            migrate_apps(apps)
