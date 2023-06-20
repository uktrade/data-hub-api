from django.core.management.base import BaseCommand
from django.db import transaction

from datahub.company.models import Advisor
from datahub.interaction.models import InteractionDITParticipant


class Command(BaseCommand):
    help = 'Merges inactive advisor with active one in interaction model'

    def add_arguments(self, parser):
        parser.add_argument('inactive_advisor_id', type=str, help='UUID of the inactive advisor')
        parser.add_argument('active_advisor_id', type=str, help='UUID of the active advisor')

    @transaction.atomic
    def handle(self, *args, **options):
        inactive_advisor_id = options['inactive_advisor_id']
        active_advisor_id = options['active_advisor_id']

        try:
            inactive_advisor = Advisor.objects.get(id=inactive_advisor_id, is_active=False)
            active_advisor = Advisor.objects.get(id=active_advisor_id, is_active=True)
        except Advisor.DoesNotExist as e:
            self.stderr.write(self.style.ERROR(str(e)))
            return

        interactions_to_update = InteractionDITParticipant.objects.filter(adviser=inactive_advisor)
        interactions_to_update.update(adviser=active_advisor)

        self.stdout.write(self.style.SUCCESS(
            f'Updated {interactions_to_update.count()} interactions from {inactive_advisor} to {active_advisor}'
        ))
