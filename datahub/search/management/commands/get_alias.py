import json
from logging import getLogger

from django.core.management.base import BaseCommand
from elasticsearch_dsl.connections import connections

logger = getLogger(__name__)


def get_alias(current_index):
    """Gets alias for current index."""
    es = connections.get_connection()
    return es.indices.get_alias(index=current_index)


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

    def handle(self, *args, **options):
        """Handle."""
        self.stdout.write(json.dumps(get_alias(options['current_index'])))
