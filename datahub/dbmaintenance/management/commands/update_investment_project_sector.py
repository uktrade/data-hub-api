from functools import lru_cache

import reversion

from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.investment.models import InvestmentProject
from datahub.metadata.models import Sector


class Command(CSVBaseCommand):
    """Command to update investment_project.sector."""

    @lru_cache(maxsize=None)
    def get_sector(self, sector_id):
        """
        :param company_id: uuid of the company
        :return: instance of Company with id == company_id if it exists,
            None otherwise
        """
        if not sector_id or sector_id.lower().strip() == 'null':
            return None
        return Sector.objects.get(id=sector_id)

    def _should_update(
        self,
        investment_project,
        old_sector,
    ):
        """
        Checks if Investment project should be updated.

        :param investment_project: instance of InvestmentProject
        :param old_sector: instance of Company or None
        :return: True if investment project needs to be updated
        """
        return (investment_project.sector == old_sector)

    def _process_row(self, row, simulate=False, **options):
        """Process one single row."""
        investment_project = InvestmentProject.objects.get(pk=row['id'])

        old_sector = self.get_sector(row['old_sector'])
        new_sector = self.get_sector(row['new_sector'])

        if self._should_update(
            investment_project,
            old_sector,
        ):
            investment_project.sector = new_sector
            if not simulate:
                with reversion.create_revision():
                    investment_project.save(
                        update_fields=(
                            'sector',
                        ),
                    )
                    reversion.set_comment('Sector migration.')
