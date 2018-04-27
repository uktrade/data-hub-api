from logging import getLogger

from django.core.management.base import BaseCommand
from django_pglocks import advisory_lock

from datahub.search.elasticsearch import init_es

logger = getLogger(__name__)


class Command(BaseCommand):
    """Command for creating the index and updating the mapping."""

    help = "Creates the Elasticsearch index (if necessary) and updates the index's mapping."

    def handle(self, *args, **options):
        """Executes the command."""
        with advisory_lock('leeloo_init_es'):
            init_es()
