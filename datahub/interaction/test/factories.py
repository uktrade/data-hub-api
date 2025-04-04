from datetime import timezone

import factory
from django.utils.timezone import now

from datahub.company.models import CompanyExportCountry
from datahub.company.test.factories import (
    AdviserFactory,
    CompanyFactory,
    ContactFactory,
    ExportFactory,
)
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
from datahub.investment.opportunity.test.factories import LargeCapitalOpportunityFactory
from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.metadata.models import Country, TradeAgreement
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
    date = factory.Faker('past_datetime', start_date='-5y', tzinfo=timezone.utc)
    notes = factory.Faker('paragraph', nb_sentences=10)
    service_id = constants.Service.inbound_referral.value.id
    archived_documents_url_path = factory.Faker('uri_path')
    was_policy_feedback_provided = False

    @to_many_field
    def contacts(self):
        """Contacts field.

        Defaults to the contact from the contact field.
        """
        return [ContactFactory(company=self.company)] if self.company else []

    @to_many_field
    def companies(self):
        """Add support for setting `companies`."""
        return [self.company] if self.company else []

    @to_many_field
    def dit_participants(self, **kwargs):
        """Instances of InteractionDITParticipant.

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

    kind = Interaction.Kind.INTERACTION
    theme = factory.Iterator(tuple(filter(None, Interaction.Theme.values)))
    communication_channel = factory.LazyFunction(
        lambda: random_obj_for_model(CommunicationChannel),
    )


class CompaniesInteractionFactory(InteractionFactoryBase):
    """Factory for creating an interaction relating to companies."""

    # TODO: this factory should be removed once `company` field is removed
    kind = Interaction.Kind.INTERACTION
    theme = factory.Iterator(tuple(filter(None, Interaction.Theme.values)))
    communication_channel = factory.LazyFunction(
        lambda: random_obj_for_model(CommunicationChannel),
    )
    company = None

    @to_many_field
    def companies(self):
        """Add support for setting `companies`."""
        return [CompanyFactory()]


class CompanyReferralInteractionFactory(CompanyInteractionFactory):
    """Factory for creating an interaction relating to a company referral."""

    company_referral = factory.RelatedFactory(
        'datahub.company_referral.test.factories.CompleteCompanyReferralFactory',
        'interaction',
        company=factory.SelfAttribute('..company'),
    )


class CompanyInteractionFactoryWithPolicyFeedback(CompanyInteractionFactory):
    """Factory for creating an interaction relating to a company, with policy feedback
    additionally provided.
    """

    kind = Interaction.Kind.INTERACTION
    communication_channel = factory.LazyFunction(
        lambda: random_obj_for_model(CommunicationChannel),
    )
    policy_feedback_notes = factory.Faker('paragraph', nb_sentences=10)
    was_policy_feedback_provided = True

    @to_many_field
    def policy_areas(self):
        """Policy areas field.

        Defaults to one random policy area.
        """
        return [random_obj_for_model(PolicyArea)]

    @to_many_field
    def policy_issue_types(self):
        """Policy issue types field.

        Defaults to one random policy issue type.
        """
        return [random_obj_for_model(PolicyIssueType)]


class InvestmentProjectInteractionFactory(InteractionFactoryBase):
    """Factory for creating an interaction relating to an investment project."""

    kind = Interaction.Kind.INTERACTION
    theme = Interaction.Theme.INVESTMENT
    investment_project = factory.SubFactory(InvestmentProjectFactory)
    communication_channel = factory.LazyFunction(
        lambda: random_obj_for_model(CommunicationChannel),
    )


class CompanyExportInteractionFactory(InteractionFactoryBase):
    """Factory for creating an interaction relating to a company export project."""

    kind = Interaction.Kind.INTERACTION
    theme = Interaction.Theme.EXPORT
    company_export = factory.SubFactory(ExportFactory)
    communication_channel = factory.LazyFunction(
        lambda: random_obj_for_model(CommunicationChannel),
    )


class LargeCapitalOpportunityInteractionFactory(InteractionFactoryBase):
    """Factory for creating an interaction relating to a large capital opportunity."""

    kind = Interaction.Kind.INTERACTION
    theme = Interaction.Theme.LARGE_CAPITAL_OPPORTUNITY
    large_capital_opportunity = factory.SubFactory(LargeCapitalOpportunityFactory)


class CompanyInteractionFactoryWithRelatedTradeAgreements(CompanyInteractionFactory):
    """Factory for creating a company interaction with related_trade_agreements."""

    has_related_trade_agreements = True

    @to_many_field
    def related_trade_agreements(self):
        """related_trade_agreements field."""
        return TradeAgreement.objects.all()[:3]


class ServiceDeliveryFactory(InteractionFactoryBase):
    """Service delivery factory."""

    kind = Interaction.Kind.SERVICE_DELIVERY
    service_delivery_status = factory.LazyFunction(
        lambda: random_obj_for_model(ServiceDeliveryStatus),
    )
    grant_amount_offered = factory.Faker(
        'pydecimal',
        left_digits=4,
        right_digits=2,
        positive=True,
    )
    net_company_receipt = factory.Faker(
        'pydecimal',
        left_digits=4,
        right_digits=2,
        positive=True,
    )

    class Meta:
        model = 'interaction.Interaction'


class EventServiceDeliveryFactory(InteractionFactoryBase):
    """Event service delivery factory."""

    kind = Interaction.Kind.SERVICE_DELIVERY
    theme = Interaction.Theme.EXPORT
    event = factory.SubFactory(EventFactory)


class InteractionDITParticipantFactory(factory.django.DjangoModelFactory):
    """Factory for a DIT participant in an interaction."""

    interaction = factory.SubFactory(
        CompanyInteractionFactory,
        dit_participants=[],
        contacts=[],
    )
    adviser = factory.SubFactory(AdviserFactory)
    team = factory.SelfAttribute('adviser.dit_team')

    class Meta:
        model = 'interaction.InteractionDITParticipant'


class InteractionExportCountryFactory(factory.django.DjangoModelFactory):
    """Factory for Interaction export country."""

    interaction = factory.SubFactory(CompanyInteractionFactory)
    country = factory.Iterator(Country.objects.all())
    status = factory.Iterator(CompanyExportCountry.Status.values)
    created_on = now()
    created_by = factory.SubFactory(AdviserFactory)

    class Meta:
        model = 'interaction.InteractionExportCountry'


class ExportCountriesInteractionFactory(CompanyInteractionFactory):
    """Factory for creating an export interaction with export countries."""

    theme = factory.Iterator([Interaction.Theme.EXPORT, Interaction.Theme.OTHER])
    were_countries_discussed = True

    @to_many_field
    def export_countries(self, **kwargs):
        """Instances of InteractionExportCountryFactory.
        Defaults to one InteractionExportCountryFactory.
        """
        return [InteractionExportCountryFactory(interaction=self, **kwargs)]


class ExportCountriesServiceDeliveryFactory(ServiceDeliveryFactory):
    """Factory for creating an export service delivery with export countries."""

    theme = factory.Iterator([Interaction.Theme.EXPORT, Interaction.Theme.OTHER])
    were_countries_discussed = True

    @to_many_field
    def export_countries(self, **kwargs):
        """Instances of InteractionExportCountryFactory.
        Defaults to one InteractionExportCountryFactory.
        """
        return [InteractionExportCountryFactory(interaction=self, **kwargs)]


class CompaniesInteractionWithExportBarrierOtherFactory(CompanyInteractionFactory):
    """Create companies interaction with export barriers - Other."""

    helped_remove_export_barrier = True
    export_barrier_notes = 'Lorem ipsum'

    @to_many_field
    def export_barrier_types(self):
        """Add "other" export barrier type."""
        return [constants.ExportBarrierType.other.value.id]


class CompaniesInteractionWithExportBarrierFinanceFactory(CompanyInteractionFactory):
    """Create companies interaction with export barriers - Finance."""

    helped_remove_export_barrier = True
    export_barrier_notes = ''

    @to_many_field
    def export_barrier_types(self):
        """Add "other" export barrier type."""
        return [constants.ExportBarrierType.finance.value.id]
