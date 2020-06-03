from logging import getLogger

import reversion
from django.utils.timezone import now

from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_uuid
from datahub.metadata.models import Sector


logger = getLogger(__name__)


class Command(CSVBaseCommand):
    """Command to disable a Sector."""

    def _process_row(self, row, simulate=False, **options):
        """Process one single row."""
        pk = parse_uuid(row['id'])
        sector = Sector.objects.get(pk=pk)

        if sector.get_children():
            logger.warning(f'Not disabling sector {sector} as it has children')
            return

        sector.disabled_on = now()

        if simulate:
            return

        with reversion.create_revision():
            sector.save(update_fields=('disabled_on',))
            reversion.set_comment('Sector disable.')
