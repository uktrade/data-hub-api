import factory
from django.utils.timezone import utc

from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory
from datahub.core import constants
from datahub.core.test_utils import random_obj_for_model
from datahub.event.test.factories import EventFactory
from datahub.interaction.models import CommunicationChannel, Interaction, ServiceDeliveryStatus
from datahub.investment.test.factories import InvestmentProjectFactory


class InteractionFactoryBase(factory.django.DjangoModelFactory):
    """Factory for creating an interaction relating to a company."""

    created_by = factory.SubFactory(AdviserFactory)
    modified_by = factory.SubFactory(AdviserFactory)
    contact = factory.SubFactory(ContactFactory)
    subject = factory.Faker('sentence', nb_words=8)
    date = factory.Faker('past_datetime', start_date='-5y', tzinfo=utc)
    notes = factory.Faker('paragraph', nb_sentences=10)
    dit_adviser = factory.SubFactory(AdviserFactory)
    service_id = constants.Service.trade_enquiry.value.id
    dit_team_id = constants.Team.healthcare_uk.value.id
    archived_documents_url_path = factory.Faker('uri_path')

    class Meta:
        model = 'interaction.Interaction'


class CompanyInteractionFactory(InteractionFactoryBase):
    """Factory for creating an interaction relating to a company."""

    kind = Interaction.KINDS.interaction
    company = factory.SubFactory(CompanyFactory)
    communication_channel = factory.LazyFunction(
        lambda: random_obj_for_model(CommunicationChannel)
    )


class InvestmentProjectInteractionFactory(InteractionFactoryBase):
    """Factory for creating an interaction relating to an investment project."""

    kind = Interaction.KINDS.interaction
    investment_project = factory.SubFactory(InvestmentProjectFactory)
    communication_channel = factory.LazyFunction(
        lambda: random_obj_for_model(CommunicationChannel)
    )


class ServiceDeliveryFactory(InteractionFactoryBase):
    """Service delivery factory."""

    kind = Interaction.KINDS.service_delivery
    company = factory.SubFactory(CompanyFactory)
    service_delivery_status = factory.LazyFunction(
        lambda: random_obj_for_model(ServiceDeliveryStatus)
    )
    grant_amount_offered = factory.Faker(
        'pydecimal', left_digits=4, right_digits=2, positive=True
    )
    net_company_receipt = factory.Faker(
        'pydecimal', left_digits=4, right_digits=2, positive=True
    )

    class Meta:
        model = 'interaction.Interaction'


class EventServiceDeliveryFactory(InteractionFactoryBase):
    """Event service delivery factory."""

    kind = Interaction.KINDS.service_delivery
    company = factory.SubFactory(CompanyFactory)
    event = factory.SubFactory(EventFactory)
