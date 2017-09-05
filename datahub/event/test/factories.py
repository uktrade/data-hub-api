import uuid

import factory

from datahub.company.test.factories import AdviserFactory
from datahub.core.constants import Country, Team
from datahub.core.test.factories import to_many_field
from datahub.event.constants import EventType, LocationType, Programme


class EventFactory(factory.django.DjangoModelFactory):
    """Event factory."""

    id = factory.LazyFunction(uuid.uuid4)
    created_by = factory.SubFactory(AdviserFactory)
    modified_by = factory.SubFactory(AdviserFactory)
    name = factory.Faker('text')
    event_type_id = EventType.seminar.value.id
    start_date = factory.Faker('date')
    location_type_id = LocationType.hq.value.id
    address_1 = factory.Faker('text')
    address_2 = factory.Faker('text')
    address_town = factory.Faker('text')
    address_postcode = factory.Faker('text')
    address_country_id = Country.united_kingdom.value.id
    notes = factory.Faker('text')
    organiser = factory.SubFactory(AdviserFactory)
    lead_team_id = Team.crm.value.id

    @to_many_field
    def teams(self):  # noqa: D102
        return [Team.crm.value.id, Team.healthcare_uk.value.id]

    @to_many_field
    def related_programmes(self):  # noqa: D102
        return [Programme.great_branded.value.id]

    class Meta:  # noqa: D101
        model = 'event.Event'
