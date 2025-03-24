from logging import getLogger

import reversion

from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_uuid
from datahub.investment.project.models import (
    FDISICGrouping,
    InvestmentSector,
)
from datahub.metadata.models import Sector

logger = getLogger(__name__)


class Command(CSVBaseCommand):
    """Command to create a new InvestmentSector object."""

    def _process_row(self, row, simulate=False, **options):
        """Process one single row."""
        sector_id = parse_uuid(row['sector_id'])
        fdi_sic_grouping_id = parse_uuid(row['fdi_sic_grouping_id'])
        matches = InvestmentSector.objects.filter(sector_id=sector_id)
        if len(matches) > 0:
            raise Exception(
                f'InvestmentSector for sector_id: {sector_id} already exists',
            )

        sector = Sector.objects.get(pk=sector_id)
        fdi_sic_grouping = FDISICGrouping.objects.get(pk=fdi_sic_grouping_id)
        investment_sector = InvestmentSector(
            sector=sector,
            fdi_sic_grouping=fdi_sic_grouping,
        )

        if simulate:
            return

        with reversion.create_revision():
            investment_sector.save()
            reversion.set_comment('InvestmentSector creation.')
