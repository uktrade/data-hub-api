from logging import getLogger

from django.conf import settings
from django.core.management.base import BaseCommand

from datahub.search.elasticsearch import get_client

logger = getLogger(__name__)


class Command(BaseCommand):
    """Command for deleting all Elasticsearch indexes matching the configured index name prefix."""

    help = """Irrevocably deletes all Elasticsearch indices under the configured index name prefix.

This is intended for use on GOV.UK PaaS as GOV.UK PaaS Elasticsearch does not allow deletions
using wildcards.

Don't use this unless you really mean to delete all of the app's indices!
"""
    confirm_msg = """
This operation cannot be undone.
Are you sure you want to do this?

    Type 'yes' to continue, or 'no' to cancel: """

    def add_arguments(self, parser):
        """
        Add no-input argument to the command.
        """
        parser.add_argument(
            '--noinput', '--no-input', action='store_false', dest='interactive',
            help='Tells Django to NOT prompt the user for input of any kind.',
        )

    def handle(self, *args, **options):
        """Executes the command."""
        interactive = options['interactive']

        client = get_client()
        index_statistics = client.cat.indices(index=f'{settings.ES_INDEX_PREFIX}-*', format='json')
        indices = sorted(item['index'] for item in index_statistics)

        if not indices:
            logger.info(f'No matching Elasticsearch indices to delete!')
            return

        formatted_index_list = '\n'.join(indices)
        logger.info(f'Deleting the following Elasticsearch indices:\n{formatted_index_list}')

        confirmed = not interactive or (input(self.confirm_msg) == 'yes')
        if confirmed:
            client.indices.delete(','.join(indices))
            logger.info('Elasticsearch indices deleted')
        else:
            logger.info('Command cancelled')
