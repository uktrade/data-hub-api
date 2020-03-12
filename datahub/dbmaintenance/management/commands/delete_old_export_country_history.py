from contextlib import ExitStack
from logging import getLogger

from dateutil.parser import isoparse
from django.core.management import BaseCommand
from django.db.transaction import atomic

from datahub.company.models import CompanyExportCountryHistory
from datahub.core.exceptions import SimulationRollback
from datahub.search.deletion import update_es_after_deletions

logger = getLogger(__name__)


class Command(BaseCommand):
    """
    Management command to delete CompanyExportCountryHistory objects dated before a
    specified timestamp.

    This is a temporary command to delete inaccurate CompanyExportCountryHistory objects
    that were accidentally created during the data migration.

    TODO: Remove this command once we've used it in production.
    """

    help = """Deletes CompanyExportCountryHistory objects dated before a specified timestamp."""
    requires_migrations_checks = True

    def add_arguments(self, parser):
        """Define extra arguments."""
        parser.add_argument(
            'timestamp',
            type=isoparse,
            help='An ISO timestamp. Records older than this will be deleted.',
        )
        parser.add_argument(
            '--simulate',
            action='store_true',
            help='Simulate the command by performing the deletions and rolling them back.',
        )

    def handle(self, *args, **options):
        """Main logic for the actual command."""
        is_simulation = options['simulate']
        timestamp = options['timestamp']

        queryset = CompanyExportCountryHistory.objects.filter(history_date__lt=timestamp)

        try:
            with ExitStack() as stack:
                if not is_simulation:
                    stack.enter_context(update_es_after_deletions())

                stack.enter_context(atomic())
                total_deleted, deletions_by_model = queryset.delete()

                logger.info(f'{total_deleted} records deleted. Breakdown by model:')
                for deletion_model, model_deletion_count in deletions_by_model.items():
                    logger.info(f'{deletion_model}: {model_deletion_count}')

                if is_simulation:
                    logger.info(f'Rolling back deletions...')
                    raise SimulationRollback()
        except SimulationRollback:
            logger.info(f'Deletions rolled back')
