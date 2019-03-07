from logging import getLogger

import reversion

from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_uuid
from datahub.investment.project.models import InvestmentProject

logger = getLogger(__name__)


class Command(CSVBaseCommand):
    """Command to unarchive and update the investment_project.status."""

    STATUS_MAP = {
        'Unarchive, change status to Abandoned': InvestmentProject.STATUSES.abandoned,
        'Unarchive, change status to Lost': InvestmentProject.STATUSES.lost,
        'Unarchive, change status to Ongoing': InvestmentProject.STATUSES.ongoing,
        'Unarchive, change status to Dormant': InvestmentProject.STATUSES.dormant,
        'Unarchive, change status to Delayed': InvestmentProject.STATUSES.delayed,
    }

    def _process_row(self, row, simulate=False, ignore_old_regions=False, **options):
        """Process one single row."""
        pk = parse_uuid(row['id'])
        investment_project = InvestmentProject.objects.get(pk=pk)

        if investment_project.archived_on:
            action_required = row['Action Required']
            if action_required in self.STATUS_MAP:
                investment_project.status = self.STATUS_MAP[action_required]
            else:
                logger.warning((
                    f'Not updating project {pk} as its desired status '
                    f'could not be derived from [{action_required}].'
                ))
                return
        else:
            logger.warning(f'Not updating project {pk} as it is already unarchived.')
            return

        if simulate:
            return

        with reversion.create_revision():
            # unarchive performs save
            investment_project.unarchive()
            reversion.set_comment('Investment Project was unarchived and has changed its status.')
