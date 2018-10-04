from logging import getLogger

import reversion

from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_uuid, parse_uuid_list
from datahub.investment.models import InvestmentProject


logger = getLogger(__name__)


class Command(CSVBaseCommand):
    """Command to update investment_project.business_activities."""

    def _process_row(self, row, simulate=False, ignore_old_regions=False, **options):
        """Processes a CSV file row."""
        pk = parse_uuid(row['id'])
        investment_project = InvestmentProject.objects.get(pk=pk)
        old_business_activity_ids = parse_uuid_list(row['old_business_activities'])
        new_business_activity_ids = parse_uuid_list(row['new_business_activities'])

        current_business_activities = investment_project.business_activities.all()
        current_business_activity_ids = {activity.pk for activity in current_business_activities}

        if current_business_activity_ids == set(new_business_activity_ids):
            return

        if current_business_activity_ids != set(old_business_activity_ids):
            logger.warning('Not updating project %s as its business activities have changed', pk)
            return

        if simulate:
            return

        with reversion.create_revision():
            investment_project.business_activities.set(new_business_activity_ids)
            reversion.set_comment('Business activities data migration correction.')
