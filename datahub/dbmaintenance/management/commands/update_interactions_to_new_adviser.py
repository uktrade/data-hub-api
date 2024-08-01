from logging import getLogger

import reversion


from django.core.management import BaseCommand

from datahub.interaction.models import InteractionDITParticipant

logger = getLogger(__name__)


class Command(BaseCommand):
    """
    Command to update an interaction to new adviser

    Example of executing this command locally:
        python manage.py update_interactions_to_new_adviser <old_adviser_id> <new_adviser_id>

    NOTE: Does not update the team of the new adviser.
    """

    help = 'Updates all the interaction associated with <old_adviser_id> to <new_adviser_id>'

    def add_arguments(self, parser):
        """Define extra arguments."""
        parser.add_argument(
            '--simulate',
            action='store_true',
            help='Simulate the command by querying for changed data but not saving changes.',
        )
        parser.add_argument(
            'old_adviser_id',
            type=str,
            help='Old adviser id whose interaction are to be moved from',
        )
        parser.add_argument(
            'new_adviser_id',
            type=str,
            help='New adviser id whose interaction are to be moved to',
        )

    def handle(self, *args, **options):
        simulate = options['simulate']

        # Old adviser for interactions to be moved from.
        old_adviser_id = options.get('old_adviser_id')

        # New adviser for interactions to be moved to.
        new_adviser_id = options.get('new_adviser_id')

        # Get all interactions associated with the new adviser so we can remove them
        # from the interactions associated with the old adviser. This is to prevent
        # updating the old adviser to the new adviser on interactions the new adviser
        # is already an adviser for. There is a unique together contraint on the model
        # to prevent the duplicate advisers on the same interactions. For example, inactive
        # John Doe's interactions being moved to an active John Doe's interactions. Both
        # inactive and active John Doe's may have been added to the same interaction
        # already so updating the inactive John interactions to the active John
        # interactions would cause a unique together constraint error.
        interaction_ids_with_new_adviser = InteractionDITParticipant.objects.filter(
            adviser_id=new_adviser_id,
        ).values_list('interaction_id', flat=True)

        interaction_participants = InteractionDITParticipant.objects.filter(
            adviser_id=old_adviser_id,
        ).exclude(interaction_id__in=interaction_ids_with_new_adviser)

        if not interaction_participants:
            logger.warning('No interactions to update.')
            return

        interaction_participants_count = interaction_participants.count()
        logger.info(
            f'{interaction_participants_count} interaction participants to update.',
        )

        # Update the adviser to the new adviser.
        for interaction_participant in interaction_participants:
            if simulate:
                logger.info(
                    f'Moving participant interaction: {interaction_participant.id} from '
                    f'current adviser: {interaction_participant.adviser_id} to '
                    f'new adviser: {new_adviser_id}',
                )
                return

            interaction_participant.adviser_id = new_adviser_id

            # Cannot bulk_update as doesn't trigger signals for reversion.
            with reversion.create_revision():
                interaction_participant.save()
                reversion.set_comment(
                    f'Updated interactions: {interaction_participants_count} to have new adviser '
                    f'id {new_adviser_id}',
                )
