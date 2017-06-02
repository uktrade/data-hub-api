from logging import getLogger

from django.core.management.base import BaseCommand
from elasticsearch_dsl.connections import connections

logger = getLogger(__name__)


def create_alias(current_index, alias_name):
    """Creates new alias for current index."""
    es = connections.get_connection()
    return es.indices.put_alias(index=current_index, name=alias_name)


class Command(BaseCommand):
    """Elasticsearch create alias command."""

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
            help='Name of alias to be created.'
        )

    def handle(self, *args, **options):
        """Handle."""
        create_alias(options['current_index'], options['alias_name'])
