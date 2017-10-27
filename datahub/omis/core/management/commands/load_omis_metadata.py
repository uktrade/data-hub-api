from pathlib import PurePath

from django.core.management import call_command
from django.core.management.base import BaseCommand


METADATA_FIXTURE_DIR = PurePath(__file__).parents[3] / 'fixtures'


class Command(BaseCommand):
    """Loads all the OMIS metadata fixtures."""

    def handle(self, *args, **options):
        """It loads all OMIS metadata fixtures."""
        call_command(
            'loaddata',
            *[
                METADATA_FIXTURE_DIR / 'service_types.yaml',
                METADATA_FIXTURE_DIR / 'cancellation_reasons.yaml',
            ]
        )
        call_command('load_initial_omis_markets')
