from pathlib import PurePath

import yaml
from django.apps import apps
from django.core.management import BaseCommand, call_command, CommandError

from datahub.metadata.fixtures import Fixture


SOURCE_ROOT = PurePath(__file__).parents[4]
SHARED_METADATA_FIXTURE_DIR = SOURCE_ROOT / 'fixtures' / 'metadata'
EVENTS_FIXTURE_DIR = SOURCE_ROOT / 'datahub' / 'event' / 'fixtures'

SHARED_FIXTURES = (
    SHARED_METADATA_FIXTURE_DIR / 'administrative_areas.yaml',
    SHARED_METADATA_FIXTURE_DIR / 'companies.yaml',
    SHARED_METADATA_FIXTURE_DIR / 'investment.yaml',
    SHARED_METADATA_FIXTURE_DIR / 'referrals.yaml',
    SHARED_METADATA_FIXTURE_DIR / 'teams.yaml',
    SHARED_METADATA_FIXTURE_DIR / 'titles.yaml',
    SHARED_METADATA_FIXTURE_DIR / 'uk_regions.yaml',
    SHARED_METADATA_FIXTURE_DIR / 'trade_agreements.yaml',
)

EVENTS_FIXTURES = (
    EVENTS_FIXTURE_DIR / 'programmes.yaml',
    EVENTS_FIXTURE_DIR / 'location_types.yaml',
    EVENTS_FIXTURE_DIR / 'event_types.yaml',
)


class ExistingDataFoundError(CommandError):
    """Error raised when existing data is found when loading metadata fixtures."""


class Command(BaseCommand):
    """Loads all the metadata fixtures."""

    help = ('Loads initial data for various metadata models. Only intended to be used in new '
            'environments, and should not be used in production. Will fail if metadata records '
            'already exist (unless --force is passed).')

    def add_arguments(self, parser):
        """Adds additional command arguments."""
        parser.add_argument(
            '--force',
            action='store_true',
            help='Load data even if there are existing records.',
        )

    def handle(self, *args, force=None, **options):
        """
        It loads all metadata fixtures.

        The algorithm could iterate and import all the files in the `metadata`
        folder but some could have dependencies so it's safer to specify the
        list manually.
        """
        registered_fixtures = Fixture.all()

        all_fixtures = (
            *SHARED_FIXTURES,
            *EVENTS_FIXTURES,
            *registered_fixtures,
        )

        if not force:
            _ensure_no_existing_data(all_fixtures)

        call_command(
            'loaddata',
            *all_fixtures,
        )


def _ensure_no_existing_data(fixtures):
    model_names_per_fixture = (_get_models_for_fixture(fixture) for fixture in fixtures)
    model_names = set().union(*model_names_per_fixture)

    for model_name in model_names:
        model = apps.get_model(model_name)
        if model.objects.exists():
            raise ExistingDataFoundError(
                f'Cannot run loadinitialmetadata when metadata already exists. Existing data '
                f'found for the {model_name} model.',
            )


def _get_models_for_fixture(path):
    with open(path, 'r') as file:
        data = yaml.safe_load(file)
        models = {item['model'] for item in data}
    return models
