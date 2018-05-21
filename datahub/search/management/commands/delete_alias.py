from logging import getLogger

from django.core.management.base import BaseCommand

from datahub.search.elasticsearch import get_client

logger = getLogger(__name__)


def delete_alias(current_index, alias_name):
    """Deletes alias for current index."""
    es = get_client()
    return es.indices.delete_alias(index=current_index, name=alias_name)


class Command(BaseCommand):
    """Elasticsearch delete alias command."""

    def add_arguments(self, parser):
        """Handle arguments."""
        parser.add_argument(
            '--current_index',
            dest='current_index',
            type=str,
            help='Current Elasticsearch index.'
        )

        parser.add_argument(
            '--alias_name',
            dest='alias_name',
            type=str,
            help='Name of alias to be deleted.'
        )

    def handle(self, *args, **options):
        """Handle."""
        delete_alias(options['current_index'], options['alias_name'])
