from logging import getLogger

from django.core.management.base import BaseCommand
from django_pglocks import advisory_lock

from datahub.search.apps import get_search_apps, get_search_apps_by_name
from datahub.search.migrate import migrate_apps

logger = getLogger(__name__)


class Command(BaseCommand):
    """Command for migrating an OpenSearch index.

    This will also create OpenSearch indices the first time it is run.
    """

    help = """Migrate modified mapping types for OpenSearch indices.

For new indices, the command creates each index and schedules a RQ task to synchronise
data to the new index.

For existing indices, the command creates new indices for modified search models
and schedules RQ tasks to synchronises data to the new indices and then delete the old
indices.

See docs/OpenSearch migrations.md for further details."""

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

        with advisory_lock('migrate-opensearch-lock-id'):
            migrate_apps(apps)
