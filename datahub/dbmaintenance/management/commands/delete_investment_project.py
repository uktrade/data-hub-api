from contextlib import ExitStack
from logging import getLogger

from django.db.transaction import atomic

from datahub.core.exceptions import SimulationRollback
from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.investment.models import InvestmentProject
from datahub.search.deletion import update_es_after_deletions

logger = getLogger(__name__)


class Command(CSVBaseCommand):
    """Command to delete investment projects."""

    def _process_row(self, row, simulate=False, **options):
        """Process one single row."""
        investment_project_id = row['id']
        investment_project = InvestmentProject.objects.get(pk=investment_project_id)

        try:
            with ExitStack() as stack:
                if not simulate:
                    stack.enter_context(update_es_after_deletions())

                stack.enter_context(atomic())
                total_deleted, deletions_by_model = investment_project.delete()
                logger.info((
                    f'{total_deleted} records deleted for investment project: '
                    f'{investment_project_id}. Breakdown by model:'
                ))
                for deletion_model, model_deletion_count in deletions_by_model.items():
                    logger.info(f'{deletion_model}: {model_deletion_count}')

                if simulate:
                    logger.info('Rolling back deletions...')
                    raise SimulationRollback()
        except SimulationRollback:
            logger.info('Deletions rolled back')
