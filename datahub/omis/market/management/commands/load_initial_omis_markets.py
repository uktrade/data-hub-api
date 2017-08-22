from pathlib import PurePath

from django.core.management import call_command
from django.core.management.base import BaseCommand

from ...models import Market


METADATA_FIXTURE_DIR = PurePath(__file__).parents[3] / 'fixtures'


class Command(BaseCommand):
    """Loads all OMIS markets."""

    def add_arguments(self, parser):
        """Handle arguments."""
        parser.add_argument(
            '--override',
            action='store_true',
            dest='override',
            default=False,
            help='Override existing values.',
        )

    def handle(self, *args, **options):
        """
        It loads the OMIS markets.
        It does not load any values if the table is not empty to avoid losing existing
        data but this can be bypassed using the argument --override
        """
        if options['override'] or not Market.objects.count():
            call_command(
                'loaddata',
                METADATA_FIXTURE_DIR / 'initial_markets.yaml',
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    'WARNING: Some OMIS markets are already present in the database '
                    'therefore no changes have been made to avoid overriding '
                    'existing values accidentally. '
                    'If you want to override them use '
                    '`python manage.py load_initial_omis_market --override`'
                )
            )
