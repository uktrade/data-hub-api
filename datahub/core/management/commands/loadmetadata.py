from pathlib import PurePath

from django.core.management import call_command
from django.core.management.base import BaseCommand


SOURCE_ROOT = PurePath(__file__).parents[4]
SHARED_METADATA_FIXTURE_DIR = SOURCE_ROOT / 'fixtures' / 'metadata'
EVENTS_FIXTURE_DIR = SOURCE_ROOT / 'datahub' / 'event' / 'fixtures'
INTERACTIONS_FIXTURE_DIR = SOURCE_ROOT / 'datahub' / 'interaction' / 'fixtures'

SHARED_FIXTURES = (
    SHARED_METADATA_FIXTURE_DIR / 'companies.yaml',
    SHARED_METADATA_FIXTURE_DIR / 'contacts.yaml',
    SHARED_METADATA_FIXTURE_DIR / 'countries.yaml',
    SHARED_METADATA_FIXTURE_DIR / 'investment.yaml',
    SHARED_METADATA_FIXTURE_DIR / 'referrals.yaml',
    SHARED_METADATA_FIXTURE_DIR / 'sectors.yaml',
    SHARED_METADATA_FIXTURE_DIR / 'services.yaml',
    SHARED_METADATA_FIXTURE_DIR / 'teams.yaml',
    SHARED_METADATA_FIXTURE_DIR / 'titles.yaml',
    SHARED_METADATA_FIXTURE_DIR / 'uk_regions.yaml',
)

EVENTS_FIXTURES = (
    EVENTS_FIXTURE_DIR / 'programmes.yaml',
    EVENTS_FIXTURE_DIR / 'location_types.yaml',
    EVENTS_FIXTURE_DIR / 'event_types.yaml',
)

INTERACTION_FIXTURES = (
    INTERACTIONS_FIXTURE_DIR / 'communication_channels.yaml',
)


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
            *SHARED_FIXTURES,
            *EVENTS_FIXTURES,
            *INTERACTION_FIXTURES,
        )
