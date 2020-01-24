import factory
from django.utils.timezone import now, utc

from datahub.company.models import CompanyExportCountry
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
from datahub.metadata.models import Country
from datahub.metadata.test.factories import ServiceFactory


class ServiceQuestionFactory(factory.django.DjangoModelFactory):
    """ServiceQuestion factory."""

    name = factory.Faker('word')
    service = factory.SubFactory(ServiceFactory)

    class Meta:
        model = 'interaction.ServiceQuestion'


class ServiceAnswerOptionFactory(factory.django.DjangoModelFactory):
    """ServiceQuestion factory."""

    name = factory.Faker('word')
    question = factory.SubFactory(ServiceQuestionFactory)

    class Meta:
        model = 'interaction.ServiceAnswerOption'


class CommunicationChannelFactory(factory.django.DjangoModelFactory):
    """CommunicationChannel factory."""

    name = factory.Faker('word')

    class Meta:
        model = 'interaction.CommunicationChannel'


class InteractionFactoryBase(factory.django.DjangoModelFactory):
    """Factory for creating an interaction relating to a company."""

    created_by = factory.SubFactory(AdviserFactory)
    modified_by = factory.SelfAttribute('created_by')
    company = factory.SubFactory(CompanyFactory)
    subject = factory.Faker('sentence', nb_words=8)
    date = factory.Faker('past_datetime', start_date='-5y', tzinfo=utc)
    notes = factory.Faker('paragraph', nb_sentences=10)
    service_id = constants.Service.inbound_referral.value.id
    archived_documents_url_path = factory.Faker('uri_path')
    was_policy_feedback_provided = False

    @to_many_field
    def contacts(self):
        """
        Contacts field.

        Defaults to the contact from the contact field.
        """
        return [ContactFactory(company=self.company)] if self.company else []

    @to_many_field
    def dit_participants(self, **kwargs):
        """
        Instances of InteractionDITParticipant.

        Defaults to one InteractionDITParticipant based on dit_adviser and dit_team.
        """
        return [
            InteractionDITParticipantFactory(
                interaction=self,
                adviser=kwargs.pop('adviser', factory.SubFactory(AdviserFactory)),
                team=kwargs.pop('team', factory.SelfAttribute('adviser.dit_team')),
                **kwargs,
            ),
        ]

    class Meta:
        model = 'interaction.Interaction'


class CompanyInteractionFactory(InteractionFactoryBase):
    """Factory for creating an interaction relating to a company."""

    kind = Interaction.KINDS.interaction
    theme = factory.Iterator(tuple(filter(None, Interaction.THEMES._db_values)))
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
    theme = Interaction.THEMES.investment
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
    theme = Interaction.THEMES.export
    event = factory.SubFactory(EventFactory)


class InteractionDITParticipantFactory(factory.django.DjangoModelFactory):
    """Factory for a DIT participant in an interaction."""

    interaction = factory.SubFactory(CompanyInteractionFactory)
    adviser = factory.SubFactory(AdviserFactory)
    team = factory.SelfAttribute('adviser.dit_team')

    class Meta:
        model = 'interaction.InteractionDITParticipant'


class InteractionExportCountryFactory(factory.django.DjangoModelFactory):
    """Factory for Interaction export country."""

    interaction = factory.SubFactory(CompanyInteractionFactory)
    country = factory.LazyFunction(lambda: random_obj_for_model(Country))
    status = factory.Iterator(tuple(CompanyExportCountry.EXPORT_INTEREST_STATUSES._db_values))
    created_on = now()
    created_by = factory.SubFactory(AdviserFactory)

    class Meta:
        model = 'interaction.InteractionExportCountry'


class ExportCountriesInteractionFactory(InteractionFactoryBase):
    """Factory for creating an export interaction with export countries."""

    kind = Interaction.KINDS.interaction
    theme = factory.Iterator([Interaction.THEMES.export, Interaction.THEMES.other])
    were_countries_discussed = True
    communication_channel = factory.LazyFunction(
        lambda: random_obj_for_model(CommunicationChannel),
    )

    @to_many_field
    def export_countries(self, **kwargs):
        """
        Instances of InteractionExportCountryFactory.
        Defaults to one InteractionExportCountryFactory.
        """
        return [
            InteractionExportCountryFactory(
                interaction=self,
                **kwargs,
            ),
        ]
