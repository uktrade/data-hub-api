from logging import getLogger, WARNING

from django.core.management.base import BaseCommand, CommandError

from datahub.search.apps import are_apps_initialised, get_search_apps, get_search_apps_by_name
from datahub.search.tasks import schedule_model_sync

logger = getLogger(__name__)


class Command(BaseCommand):
    """OpenSearch sync command."""

    def add_arguments(self, parser):
        """Handle arguments."""
        # TODO: This argument is actually the search app name, not the model name, and
        #  the argument should therefore be renamed
        parser.add_argument(
            '--model',
            action='append',
            choices=[search_app.name for search_app in get_search_apps()],
            help='Search model to import. If empty, it imports all',
        )
        parser.add_argument(
            '--foreground',
            action='store_true',
            help='If specified, the command runs in the foreground without needing RQ '
                 'running. (By default, it runs asynchronously using RQ.)',
        )

    def handle(self, *args, **options):
        """Handle."""
        getLogger('opensearch').setLevel(WARNING)

        apps = get_search_apps_by_name(options['model'])

        if not are_apps_initialised(apps):
            raise CommandError(
                'Index and mapping not initialised, please run `migrate_search` first.',
            )

        for app in apps:
            task_args = (app.name,)

            schedule_model_sync(task_args)

        logger.info('OpenSearch sync complete!')
