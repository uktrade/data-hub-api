from logging import getLogger

import reversion

from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_uuid
from datahub.investment.project.models import InvestmentProject
from datahub.metadata.models import Sector
from datahub.search.signals import disable_search_signal_receivers

logger = getLogger(__name__)


class Command(CSVBaseCommand):
    """Command to update InvestmentProject.sector."""

    @disable_search_signal_receivers(InvestmentProject)
    def _handle(self, *args, **options):
        """
        Disables search signal receivers for investment projects.
        Avoid queuing huge number of Celery tasks for syncing investment projects to Elasticsearch.
        (Syncing can be manually performed afterwards using sync_es if required.)
        """
        return super()._handle(*args, **options)

    def _process_row(self, row, simulate=False, overwrite=False, **options):
        """Process a single row."""
        pk = parse_uuid(row['id'])
        investment_project = InvestmentProject.objects.get(pk=pk)
        old_sector_id = parse_uuid(row['old_sector_id'])
        new_sector_id = parse_uuid(row['new_sector_id'])

        if any(
            [
                investment_project.sector.pk != old_sector_id,
                investment_project.sector.pk == new_sector_id,
            ]
        ):
            logger.warning(
                f'Not updating investment project {investment_project} as its',
                'sector has not changed',
            )
            return

        investment_project.sector = Sector.objects.get(pk=new_sector_id)

        if simulate:
            return

        with reversion.create_revision():
            investment_project.save(update_fields=('sector',))
            reversion.set_comment('InvestmentProject sector correction.')
