import factory
from django.utils.timezone import now

from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory
from datahub.core import constants
from datahub.event.test.factories import EventFactory
from datahub.interaction.models import Interaction
from datahub.metadata.test.factories import ServiceFactory, TeamFactory


class ServiceOfferFactory(factory.django.DjangoModelFactory):
    """Service Offer factory."""

    service = factory.SubFactory(ServiceFactory)
    dit_team = factory.SubFactory(TeamFactory)

    class Meta:
        model = 'interaction.ServiceOffer'


class InteractionFactory(factory.django.DjangoModelFactory):
    """Interaction factory."""

    kind = Interaction.KINDS.interaction
    created_by = factory.SubFactory(AdviserFactory)
    modified_by = factory.SubFactory(AdviserFactory)
    company = factory.SubFactory(CompanyFactory)
    contact = factory.SubFactory(ContactFactory)
    subject = factory.Faker('sentence', nb_words=8)
    date = now()
    notes = factory.Faker('paragraph', nb_sentences=10)
    dit_adviser = factory.SubFactory(AdviserFactory)
    service_id = constants.Service.trade_enquiry.value.id
    dit_team_id = constants.Team.healthcare_uk.value.id
    created_on = now()
    communication_channel_id = constants.InteractionType.face_to_face.value.id

    class Meta:
        model = 'interaction.Interaction'


class ServiceDeliveryFactory(factory.django.DjangoModelFactory):
    """Service delivery factory."""

    kind = Interaction.KINDS.service_delivery
    created_by = factory.SubFactory(AdviserFactory)
    modified_by = factory.SubFactory(AdviserFactory)
    company = factory.SubFactory(CompanyFactory)
    contact = factory.SubFactory(ContactFactory)
    event = factory.SubFactory(EventFactory)
    subject = factory.Faker('sentence', nb_words=8)
    date = now()
    notes = factory.Faker('paragraph', nb_sentences=10)
    dit_adviser = factory.SubFactory(AdviserFactory)
    service_id = constants.Service.trade_enquiry.value.id
    dit_team_id = constants.Team.healthcare_uk.value.id
    created_on = now()

    class Meta:
        model = 'interaction.Interaction'


class LegacyServiceDeliveryFactory(factory.django.DjangoModelFactory):
    """Legacy service delivery factory."""

    created_by = factory.SubFactory(AdviserFactory)
    modified_by = factory.SubFactory(AdviserFactory)
    company = factory.SubFactory(CompanyFactory)
    contact = factory.SubFactory(ContactFactory)
    subject = 'foo'
    date = now()
    notes = 'Bar'
    dit_adviser = factory.SubFactory(AdviserFactory)
    created_on = now()
    status_id = constants.ServiceDeliveryStatus.offered.value.id
    uk_region_id = constants.UKRegion.east_midlands.value.id
    feedback = 'foobar'

    class Meta:
        model = 'interaction.ServiceDelivery'
