from logging import getLogger

from django.core.management.base import BaseCommand, CommandError
from django_pglocks import advisory_lock

from datahub.search.apps import are_apps_initialised, get_search_apps, get_search_apps_by_name
from datahub.search.migrate import migrate_apps

logger = getLogger(__name__)


class Command(BaseCommand):
    """
    Command for migrating an Elasticsearch index.

    At present, init_es must be run before this command, but the intention is to merge these two
    commands at a later time.
    """

    help = """Migrates the mapping for Elasticsearch indices.

This creates new indices for modified search models, synchronises data to the new indices and \
then deletes the old indices.

init_es must be run before this command.

See docs/Elasticsearch migrations.md for further details."""

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
                f'Index and mapping not initialised, please run `init_es` first.',
            )

        with advisory_lock('leeloo_migrate_es'):
            migrate_apps(apps)
