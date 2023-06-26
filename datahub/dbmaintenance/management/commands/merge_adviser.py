from django.core.management.base import BaseCommand
from django.db import transaction

from datahub.company.models import Advisor
from datahub.company.models import OneListCoreTeamMember
from datahub.company_referral.models import CompanyReferral
from datahub.event.models import Event
from datahub.interaction.models import InteractionDITParticipant
from datahub.investment.investor_profile.models import LargeCapitalInvestorProfile
from datahub.investment.opportunity.models import LargeCapitalOpportunity
from datahub.investment.project.proposition.models import PropositionDocumentPermission
from datahub.user.company_list.models import CompanyList, PipelineItem
from datahub.user_event_log.models import UserEvent


class Command(BaseCommand):
    help = 'Merges inactive advisor with active in all models, then deletes the inactive advisor'

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

        # Dictionary of models and their respective fields that refer to Advisor
        model_fields_dict = {
            InteractionDITParticipant: ['adviser'],
            OneListCoreTeamMember: ['adviser'],
            CompanyReferral: ['recipient', 'completed_by'],
            Event: ['organiser'],
            LargeCapitalInvestorProfile: ['required_checks_conducted_by'],
            LargeCapitalOpportunity: ['required_checks_conducted_by'],
            PropositionDocumentPermission: ['adviser'],
            CompanyList: ['adviser'],
            PipelineItem: ['adviser'],
            UserEvent: ['adviser'],
        }

        for model, fields in model_fields_dict.items():
            for field in fields:
                instances_to_update = model.objects.filter(**{field: inactive_advisor})
                self.stdout.write(self.style.SUCCESS(
                    f'{instances_to_update.count()} instances of {model.__name__} will be updated'  # noqa
                ))
                instances_to_update.update(**{field: active_advisor})
                self.stdout.write(self.style.SUCCESS(
                    f'Successfully merged {model.__name__} instances from adviser {inactive_advisor_id} into {active_advisor_id}'  # noqa
                ))

        # Once all instances have been updated, delete the inactive advisor
        inactive_advisor.delete()

        self.stdout.write(self.style.SUCCESS(
            f'Successfully deleted inactive advisor {inactive_advisor_id}'  # noqa
        ))
