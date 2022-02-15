from logging import getLogger

import reversion

from datahub.company.models import Company
from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_uuid
from datahub.metadata.models import Sector
from datahub.search.signals import disable_search_signal_receivers

logger = getLogger(__name__)


class Command(CSVBaseCommand):
    """Command to update Company.sector."""

    @disable_search_signal_receivers(Company)
    def _handle(self, *args, **options):
        """
        Disables search signal receivers for companies.
        Avoid queuing a huge number of Celery tasks for syncing companies to OpenSearch.
        (Syncing can be manually performed afterwards using sync_es if required.)
        """
        return super()._handle(*args, **options)

    def _process_row(self, row, simulate=False, **options):
        """Process a single row."""
        pk = parse_uuid(row['id'])
        company = Company.objects.get(pk=pk)
        old_sector_id = parse_uuid(row['old_sector_id'])
        new_sector_id = parse_uuid(row['new_sector_id'])

        if any([company.sector.pk != old_sector_id, company.sector.pk == new_sector_id]):
            logger.warning(
                f'Not updating company {company} as its sector has not changed',
            )
            return

        company.sector = Sector.objects.get(pk=new_sector_id)

        if simulate:
            return

        with reversion.create_revision():
            company.save(update_fields=('sector',))
            reversion.set_comment('Company sector correction.')
