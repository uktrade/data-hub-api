import factory

from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory
from datahub.core import constants
from datahub.event.test.factories import EventFactory
from datahub.interaction.models import Interaction


class InteractionFactory(factory.django.DjangoModelFactory):
    """Interaction factory."""

    kind = Interaction.KINDS.interaction
    created_by = factory.SubFactory(AdviserFactory)
    modified_by = factory.SubFactory(AdviserFactory)
    company = factory.SubFactory(CompanyFactory)
    contact = factory.SubFactory(ContactFactory)
    subject = factory.Faker('sentence', nb_words=8)
    date = factory.Faker('past_date', start_date='-5y')
    notes = factory.Faker('paragraph', nb_sentences=10)
    dit_adviser = factory.SubFactory(AdviserFactory)
    service_id = constants.Service.trade_enquiry.value.id
    dit_team_id = constants.Team.healthcare_uk.value.id
    communication_channel_id = constants.InteractionType.face_to_face.value.id
    archived_documents_url_path = factory.Faker('uri_path')

    class Meta:
        model = 'interaction.Interaction'


class ServiceDeliveryFactory(factory.django.DjangoModelFactory):
    """Service delivery factory."""

    kind = Interaction.KINDS.service_delivery
    created_by = factory.SubFactory(AdviserFactory)
    modified_by = factory.SubFactory(AdviserFactory)
    company = factory.SubFactory(CompanyFactory)
    contact = factory.SubFactory(ContactFactory)
    event = None
    subject = factory.Faker('sentence', nb_words=8)
    date = factory.Faker('past_date', start_date='-5y')
    notes = factory.Faker('paragraph', nb_sentences=10)
    dit_adviser = factory.SubFactory(AdviserFactory)
    service_id = constants.Service.trade_enquiry.value.id
    dit_team_id = constants.Team.healthcare_uk.value.id
    archived_documents_url_path = factory.Faker('uri_path')

    class Meta:
        model = 'interaction.Interaction'


class EventServiceDeliveryFactory(ServiceDeliveryFactory):
    """Event service delivery factory."""

    event = factory.SubFactory(EventFactory)
