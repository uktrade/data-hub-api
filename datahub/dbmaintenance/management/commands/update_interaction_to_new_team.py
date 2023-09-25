from logging import getLogger

import reversion

from django.core.management.base import BaseCommand

from datahub.dbmaintenance.utils import parse_uuid, parse_uuid_list
from datahub.interaction.models import Interaction

logger = getLogger(__name__)


class Command(BaseCommand):
    """Command to update an interaction advisers to a new team"""

    help = 'Updates interaction advisers to a new team with the history up to a certain date'

    def _process_row(self, row, simulate=False):
        """Processes a CSV file row."""
        pk = parse_uuid(row['id'])
        interaction = Interaction.objects.get(pk=pk)
        team_id = parse_uuid(row['team_id'])
        adviser_ids = parse_uuid_list(row['adviser_id'])
        new_team_name = parse_uuid(row['team_name'])

        if interaction.adviser == set(adviser_ids):
            interaction.update(team=team_id)

        if simulate:
            return

        reversion.set_comment(
            'Set the advisers: ' + adviser_ids + ' to the team: ' + new_team_name
            + ' for the given interaction: ' + pk)
