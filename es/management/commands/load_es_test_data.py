from django.core.management.base import BaseCommand, CommandError

from es.services import write_to_es
from es.utils import get_elasticsearch_client


class Command(BaseCommand):
    help = 'Import dummy data into ES.'

    def handle(self, *args, **options):
        pass
