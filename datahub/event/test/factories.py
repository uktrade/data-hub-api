import factory
from django.utils.timezone import utc

from datahub.company.test.factories import AdviserFactory
from datahub.core.constants import Country, Service, Team, UKRegion
from datahub.core.test.factories import to_many_field
from datahub.event.constants import EventType, LocationType, Programme


class EventFactory(factory.django.DjangoModelFactory):
    """Event factory."""

    created_by = factory.SubFactory(AdviserFactory)
    modified_by = factory.SelfAttribute('created_by')
    name = factory.Faker('text')
    event_type_id = EventType.seminar.value.id
    start_date = factory.Faker('date_object')
    end_date = factory.LazyAttribute(lambda event: event.start_date)
    location_type_id = LocationType.hq.value.id
    address_1 = factory.Faker('text')
    address_2 = factory.Faker('text')
    address_town = factory.Faker('text')
    address_postcode = factory.Faker('text')
    address_country_id = Country.united_kingdom.value.id
    uk_region_id = UKRegion.east_of_england.value.id
    notes = factory.Faker('text')
    organiser = factory.SubFactory(AdviserFactory)
    lead_team_id = Team.crm.value.id
    service_id = Service.inbound_referral.value.id
    archived_documents_url_path = factory.Faker('uri_path')

    @to_many_field
    def teams(self):  # noqa: D102
        return [Team.crm.value.id, Team.healthcare_uk.value.id]

    @to_many_field
    def related_programmes(self):  # noqa: D102
        return [Programme.great_branded.value.id]

    class Meta:
        model = 'event.Event'


class DisabledEventFactory(EventFactory):
    """Disabled event factory."""

    disabled_on = factory.Faker('past_datetime', tzinfo=utc)
