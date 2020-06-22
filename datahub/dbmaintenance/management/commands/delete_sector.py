from logging import getLogger

from datahub.cleanup.query_utils import get_unreferenced_objects_query
from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_uuid
from datahub.metadata.models import Sector


logger = getLogger(__name__)


class Command(CSVBaseCommand):
    """Command to delete Sector."""

    def _handle(self, *args, **options):
        """
        Get unreferenced sectors and store in variable for use in _process_row.
        This avoids having to call the same query for each row in the csv.
        """
        self.unreferenced_sectors = get_unreferenced_objects_query(Sector).all()
        return super()._handle(*args, **options)

    def _process_row(self, row, simulate=False, **options):
        """Process one single row."""
        pk = parse_uuid(row['id'])
        sector = Sector.objects.get(pk=pk)

        # Check that the sector is not referenced by any objects:
        if sector not in self.unreferenced_sectors:
            logger.warning(f'Not deleting sector {sector} as it is referenced by another object')
            return

        if simulate:
            return

        # This will attempt to delete all descendants as well, but as the
        # parent foreign key relationship is protected it will fail.
        # Therefore, children must be deleted before attempting to delete
        # their parent.
        sector.delete()
