from pathlib import PurePath

from django.core.management import call_command
from django.core.management.base import BaseCommand


METADATA_FIXTURE_DIR = PurePath(__file__).parents[4] / 'fixtures/metadata'


class Command(BaseCommand):
    """Loads all the metadata fixtures."""

    def handle(self, *args, **options):
        """
        It loads all metadata fixtures.

        The algorithm could iterate and import all the files in the `metadata`
        folder but some could have dependencies so it's safer to specify the
        list manually.
        """
        call_command(
            'loaddata',
            *[
                METADATA_FIXTURE_DIR / 'companies.yaml',
                METADATA_FIXTURE_DIR / 'contacts.yaml',
                METADATA_FIXTURE_DIR / 'countries.yaml',
                METADATA_FIXTURE_DIR / 'interactions.yaml',
                METADATA_FIXTURE_DIR / 'investment.yaml',
                METADATA_FIXTURE_DIR / 'referrals.yaml',
                METADATA_FIXTURE_DIR / 'sectors.yaml',
                METADATA_FIXTURE_DIR / 'services.yaml',
                METADATA_FIXTURE_DIR / 'teams.yaml',
                METADATA_FIXTURE_DIR / 'titles.yaml',
                METADATA_FIXTURE_DIR / 'uk_regions.yaml',
                METADATA_FIXTURE_DIR / 'omis.yaml',
            ]
        )
