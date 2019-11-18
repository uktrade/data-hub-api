from logging import getLogger

import reversion

from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_choice, parse_uuid
from datahub.investment.project.models import InvestmentProject


logger = getLogger(__name__)


class Command(CSVBaseCommand):
    """Command to update investment_project.status."""

    help = """
    Update the statuses of investment projects using a CSV file containing
    'id' and 'status' columns.
    """

    def _process_row(self, row, simulate=False, **options):
        """Process one single row."""
        pk = parse_uuid(row['id'])
        investment_project = InvestmentProject.objects.get(pk=pk)
        status = parse_choice(row['status'], InvestmentProject.STATUSES)

        if investment_project.status == status:
            return

        investment_project.status = status

        if simulate:
            return

        with reversion.create_revision():
            investment_project.save(update_fields=('status',))
            reversion.set_comment('Bulk status update.')
