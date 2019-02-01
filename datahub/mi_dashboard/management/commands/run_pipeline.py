from logging import getLogger

from django.core.management.base import BaseCommand

from datahub.mi_dashboard.pipelines import run_mi_investment_project_etl_pipeline

logger = getLogger(__name__)


class Command(BaseCommand):
    """Command for running the MI dashboard pipeline."""

    help = """It updates all investment projects in the MI database. It should be run after a
change has been made to the schema.
"""

    def handle(self, *args, **options):
        """Executes the command."""
        updated, created = run_mi_investment_project_etl_pipeline()
        logger.info(f'Updated "{updated}" and created "{created}" investment projects.')
