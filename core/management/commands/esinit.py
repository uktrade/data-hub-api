from django.conf import settings
from django.core.management import BaseCommand


class Command(BaseCommand):
    help = 'Defines the mapping for ES.'

    def handle(self, *args, **kwargs):
        pass
