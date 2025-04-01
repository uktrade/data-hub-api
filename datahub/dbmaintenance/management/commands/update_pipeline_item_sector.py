from logging import getLogger

import reversion

from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_uuid
from datahub.metadata.models import Sector
from datahub.user.company_list.models import PipelineItem

logger = getLogger(__name__)


class Command(CSVBaseCommand):
    """Command to update PipelineItem.sector."""

    def _process_row(self, row, simulate=False, **options):
        """Process a single row."""
        pk = parse_uuid(row['id'])
        pipeline_item = PipelineItem.objects.get(pk=pk)
        old_sector_id = parse_uuid(row['old_sector_id'])
        new_sector_id = parse_uuid(row['new_sector_id'])

        if any(
            [
                pipeline_item.sector.pk != old_sector_id,
                pipeline_item.sector.pk == new_sector_id,
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
