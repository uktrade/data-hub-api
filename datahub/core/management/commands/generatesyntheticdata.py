import os
import sys
import time
from pathlib import PurePath

from django.core.management import BaseCommand, call_command, CommandError

from datahub.company.models import (
    Advisor,
    Company,
    Contact,
)
from datahub.company.test.factories import AdviserFactory, ContactFactory
from datahub.core.test_utils import random_obj_for_model
from datahub.interaction.test.factories import CompanyInteractionFactory


SOURCE_ROOT = PurePath(__file__).parents[4]


class ExistingDataFoundError(CommandError):
    """Error raised when existing data is found when loading metadata fixtures."""


class Command(BaseCommand):
    """
    Generates various synthetic data to populate the database on a new environment.
    """

    help = (
        'Generates various synthetic data to populate the database on a new environment.'
        'Will fail if company records already exist (unless --force is passed).'
        'Should not be used in production'
    )

    def add_arguments(self, parser):
        """
        Adds additional command arguments.
        """
        parser.add_argument(
            'number_of_companies',
            type=int,
            help='Number of companies to be generated. Default is 100',
            nargs='?',
            default=100,
        )

        parser.add_argument(
            'number_of_advisers',
            type=int,
            help='Number of advisers to be generated. Default is 50',
            nargs='?',
            default=50,
        )

        parser.add_argument(
            'number_of_interactions',
            type=int,
            help='Number of interactions to be generated. Default is 300',
            nargs='?',
            default=300,
        )

        parser.add_argument(
            '--force',
            action='store_true',
            help='Load data even if there are existing records.',
        )

    def handle(self, *args, force=None, **options):
        """
        Handle invocation of the command.
        """
        if not force and Company.objects.exists():
            raise ExistingDataFoundError(
                f'Cannot run generatesyntehticdata when data exists. Existing data '
                f'found for the Company model.',
            )

        start_time = time.time()

        number_of_companies = options['number_of_companies']
        number_of_advisers = options['number_of_advisers']
        number_of_interactions = options['number_of_interactions']
        db_name = os.environ['DATABASE_URL']

        # change to test db and generate the preparation fixtures
        os.environ['DATABASE_URL'] = '%s/test_%s' % (
            db_name.rsplit('/', 1)[0], db_name.rsplit('/', 1)[1],
        )

        for _ in range(number_of_companies):
            ContactFactory.create()

        for _ in range(number_of_advisers):
            AdviserFactory.create()

        preparation_fixture = (SOURCE_ROOT / 'preparation_data.yaml')
        _dump_fixture_data(preparation_fixture)

        self.stdout.write(self.style.WARNING('Finished generating companies and advisers...'))

        # load preparation fixtures into the test db
        call_command(
            'loaddata',
            preparation_fixture,
        )

        # generate the interactions using the previously generated companies, models and contacts
        for _ in range(number_of_interactions):
            contact = random_obj_for_model(Contact)
            adviser = random_obj_for_model(Advisor)
            CompanyInteractionFactory(
                dit_participants__adviser=adviser,
                created_by=adviser,
                contacts=[contact],
                company=contact.company,
            )

        fixture = (SOURCE_ROOT / 'initial_data.yaml')

        # generate the main fixture
        _dump_fixture_data(fixture)

        # switch back to the main db
        os.environ['DATABASE_URL'] = db_name

        # lock and load ...
        call_command(
            'loaddata',
            fixture,
        )

        # remove the fixture files and log the elapsed time
        os.remove(preparation_fixture)

        # replace this with the S3 export command
        os.remove(fixture)

        self.stdout.write(
            self.style.SUCCESS('All done in %s seconds' % (time.time() - start_time)),
        )


def _dump_fixture_data(fixture_path):

    sysout = sys.stdout
    sys.stdout = open(fixture_path, 'w')

    call_command(
        'dumpdata',
    )
    sys.stdout = sysout
