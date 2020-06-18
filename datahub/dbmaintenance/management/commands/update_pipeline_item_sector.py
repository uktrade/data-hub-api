from logging import getLogger

import reversion

from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_uuid
from datahub.metadata.models import Sector
from datahub.search.signals import disable_search_signal_receivers
from datahub.user.company_list.models import PipelineItem

logger = getLogger(__name__)


class Command(CSVBaseCommand):
    """Command to update PipelineItem.sector."""

    @disable_search_signal_receivers(PipelineItem)
    def _handle(self, *args, **options):
        """
        Disables search signal receivers for pipeline items.
        Avoid queuing huge number of Celery tasks for syncing pipeline items to Elasticsearch.
        (Syncing can be manually performed afterwards using sync_es if required.)
        """
        return super()._handle(*args, **options)

    def _process_row(self, row, simulate=False, overwrite=False, **options):
        """Process a single row."""
        pk = parse_uuid(row['id'])
        pipeline_item = PipelineItem.objects.get(pk=pk)
        old_sector_id = parse_uuid(row['old_sector_id'])
        new_sector_id = parse_uuid(row['new_sector_id'])

        if any(
            [
                pipeline_item.sector.pk != old_sector_id, pipeline_item.sector.pk == new_sector_id,
            ],
        ):
            logger.warning(
                f'Not updating PipelineItem {pipeline_item} as its sector has not changed',
            )
            return

        pipeline_item.sector = Sector.objects.get(pk=new_sector_id)

        if simulate:
            return

        with reversion.create_revision():
            pipeline_item.save(update_fields=('sector',))
            reversion.set_comment('PipelineItem sector correction.')
