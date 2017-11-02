from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Loads all the OMIS metadata fixtures."""

    def handle(self, *args, **options):
        """It loads all OMIS metadata fixtures."""
        call_command('load_initial_omis_markets')
