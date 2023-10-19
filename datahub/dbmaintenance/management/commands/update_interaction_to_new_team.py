from logging import getLogger

import reversion

from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_uuid
from datahub.interaction.models import InteractionDITParticipant

logger = getLogger(__name__)


class Command(CSVBaseCommand):
    """
    Command to update an interaction advisers to a new team.

    Requires a CSV with a row of interaction ids to update.
    Must specify a `team_id` for updating the team on the InteractionDITParticipant.
    """

    help = 'Updates interaction advisers to a new team with the history up to a certain date'

    def add_arguments(self, parser):
        """Define extra arguments."""
        super().add_arguments(parser)
        parser.add_argument('team_id', type=str,
                            help='team id to move the interaction to a new team')

    def _process_row(self, row, simulate=False, **options):
        """Processes a CSV file row."""
        interaction_pk = parse_uuid(row['id'])

        # Team to move to.
        team_id = options.get('team_id')

        if not team_id:
            logger.warning('You must specify a team id')
            return

        # All advisers for the current interaction which are not already in the
        # correct team.
        interaction_participants = InteractionDITParticipant.objects.filter(
            interaction_id=interaction_pk,
        ).exclude(
            team_id=team_id,
        ).select_related('team', 'adviser')

        if not interaction_participants:
            logger.warning(f'No interaction participants for interaction: {interaction_pk}')
            return

        logger.info(f'{interaction_participants.count()} participants to update.')

        # Update the team for each adviser on the current interaction.
        for interaction_participant in interaction_participants:
            if simulate:
                logger.info(
                    f'{interaction_participant.adviser} - {interaction_participant.team_id}:'
                    f'{interaction_participant.team}',
                )
            interaction_participant.team_id = team_id

        # Prevent DB changes for simulation.
        if simulate:
            return

        # Bulk update all adviser teams.
        with reversion.create_revision():
            InteractionDITParticipant.objects.bulk_update(
                interaction_participants, ['team'],
            )
            reversion.set_comment(
                f'Updated interaction {interaction_pk} participants to have team id {team_id}',
            )
