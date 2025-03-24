from logging import getLogger

import reversion

from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_uuid
from datahub.investment.project.models import InvestmentSector

logger = getLogger(__name__)


class Command(CSVBaseCommand):
    """Command to delete an InvestmentSector object."""

    def _process_row(self, row, simulate=False, **options):
        """Process one single row."""
        sector_id = parse_uuid(row['sector_id'])
        fdi_sic_grouping_id = parse_uuid(row['fdi_sic_grouping_id'])
        matches = InvestmentSector.objects.filter(
            sector_id=sector_id,
            fdi_sic_grouping_id=fdi_sic_grouping_id,
        )
        if len(matches) == 0:
            error_msg = (
                'InvestmentSector does not exist\n'
                'sector_id: {0}'
                'fdi_sic_grouping_id: {1}'
            ).format(sector_id, fdi_sic_grouping_id)
            raise Exception(error_msg)

        if simulate:
            return

        with reversion.create_revision():
            matches.delete()
            reversion.set_comment('InvestmentSector deletion.')
