import factory
from django.utils.timezone import utc

from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory
from datahub.core import constants
from datahub.core.test.factories import to_many_field
from datahub.core.test_utils import random_obj_for_model
from datahub.event.test.factories import EventFactory
from datahub.interaction.models import (
    CommunicationChannel,
    Interaction,
    PolicyArea,
    PolicyIssueType,
    ServiceDeliveryStatus,
)
from datahub.investment.project.test.factories import InvestmentProjectFactory


class InteractionFactoryBase(factory.django.DjangoModelFactory):
    """Factory for creating an interaction relating to a company."""

    created_by = factory.SubFactory(AdviserFactory)
    modified_by = factory.SubFactory(AdviserFactory)
    company = factory.SubFactory(CompanyFactory)
    contact = factory.SubFactory(
        ContactFactory,
        company=factory.SelfAttribute('..company'),
    )
    subject = factory.Faker('sentence', nb_words=8)
    date = factory.Faker('past_datetime', start_date='-5y', tzinfo=utc)
    notes = factory.Faker('paragraph', nb_sentences=10)
    dit_adviser = factory.SubFactory(AdviserFactory)
    service_id = constants.Service.trade_enquiry.value.id
    dit_team = factory.SelfAttribute('dit_adviser.dit_team')
    archived_documents_url_path = factory.Faker('uri_path')
    was_policy_feedback_provided = False

    @to_many_field
    def contacts(self):
        """
        Contacts field.

        Defaults to the contact from the contact field.
        """
        return [self.contact] if self.contact else []

    @to_many_field
    def dit_participants(self):
        """
        Instances of InteractionDITParticipant.

        Defaults to one InteractionDITParticipant based on dit_adviser and dit_team.
        """
        return [
            InteractionDITParticipantFactory(
                interaction=self,
                adviser=self.dit_adviser,
                team=self.dit_team,
            ),
        ]

    class Meta:
        model = 'interaction.Interaction'


class CompanyInteractionFactory(InteractionFactoryBase):
    """Factory for creating an interaction relating to a company."""

    kind = Interaction.KINDS.interaction
    communication_channel = factory.LazyFunction(
        lambda: random_obj_for_model(CommunicationChannel),
    )


class CompanyInteractionFactoryWithPolicyFeedback(CompanyInteractionFactory):
    """
    Factory for creating an interaction relating to a company, with policy feedback
    additionally provided.
    """

    kind = Interaction.KINDS.interaction
    communication_channel = factory.LazyFunction(
        lambda: random_obj_for_model(CommunicationChannel),
    )
    policy_feedback_notes = factory.Faker('paragraph', nb_sentences=10)
    was_policy_feedback_provided = True

    @to_many_field
    def policy_areas(self):
        """
        Policy areas field.

        Defaults to one random policy area.
        """
        return [random_obj_for_model(PolicyArea)]

    @to_many_field
    def policy_issue_types(self):
        """
        Policy issue types field.

        Defaults to one random policy issue type.
        """
        return [random_obj_for_model(PolicyIssueType)]


class InvestmentProjectInteractionFactory(InteractionFactoryBase):
    """Factory for creating an interaction relating to an investment project."""

    kind = Interaction.KINDS.interaction
    investment_project = factory.SubFactory(InvestmentProjectFactory)
    communication_channel = factory.LazyFunction(
        lambda: random_obj_for_model(CommunicationChannel),
    )


class ServiceDeliveryFactory(InteractionFactoryBase):
    """Service delivery factory."""

    kind = Interaction.KINDS.service_delivery
    service_delivery_status = factory.LazyFunction(
        lambda: random_obj_for_model(ServiceDeliveryStatus),
    )
    grant_amount_offered = factory.Faker(
        'pydecimal', left_digits=4, right_digits=2, positive=True,
    )
    net_company_receipt = factory.Faker(
        'pydecimal', left_digits=4, right_digits=2, positive=True,
    )

    class Meta:
        model = 'interaction.Interaction'


class EventServiceDeliveryFactory(InteractionFactoryBase):
    """Event service delivery factory."""

    kind = Interaction.KINDS.service_delivery
    event = factory.SubFactory(EventFactory)


class InteractionDITParticipantFactory(factory.django.DjangoModelFactory):
    """Factory for a DIT participant in an interaction."""

    interaction = factory.SubFactory(
        CompanyInteractionFactory,
        dit_adviser=factory.SelfAttribute('..adviser'),
        dit_team=factory.SelfAttribute('..team'),
    )
    adviser = factory.SubFactory(AdviserFactory)
    team = factory.SelfAttribute('adviser.dit_team')

    class Meta:
        model = 'interaction.InteractionDITParticipant'
