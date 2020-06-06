from logging import getLogger

import reversion

from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_datetime, parse_uuid
from datahub.metadata.models import Sector


logger = getLogger(__name__)


class Command(CSVBaseCommand):
    """Command to disable a Sector."""

    def _process_row(self, row, simulate=False, **options):
        """Process one single row."""
        pk = parse_uuid(row['id'])
        disabled_on = parse_datetime(row['disabled_on'])
        sector = Sector.objects.get(pk=pk)

        for descendant in sector.get_descendants(include_self=True):
            descendant.disabled_on = disabled_on

            if simulate:
                return

            with reversion.create_revision():
                descendant.save(update_fields=('disabled_on',))
                reversion.set_comment('Sector disable.')
