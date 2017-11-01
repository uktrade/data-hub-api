from pathlib import PurePath

from django.core.management import call_command
from django.core.management.base import BaseCommand

from datahub.metadata.fixtures import Fixture


SOURCE_ROOT = PurePath(__file__).parents[4]
SHARED_METADATA_FIXTURE_DIR = SOURCE_ROOT / 'fixtures' / 'metadata'
EVENTS_FIXTURE_DIR = SOURCE_ROOT / 'datahub' / 'event' / 'fixtures'
INVESTMENTS_FIXTURE_DIR = SOURCE_ROOT / 'datahub' / 'investment' / 'fixtures'

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

INVESTMENTS_FIXTURES = (
    INVESTMENTS_FIXTURE_DIR / 'investor_types.yaml',
    INVESTMENTS_FIXTURE_DIR / 'involvements.yaml',
    INVESTMENTS_FIXTURE_DIR / 'specific_programmes.yaml',
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
        registered_fixtures = Fixture.all()

        call_command(
            'loaddata',
            *SHARED_FIXTURES,
            *EVENTS_FIXTURES,
            *INVESTMENTS_FIXTURES,
            *registered_fixtures,
        )
