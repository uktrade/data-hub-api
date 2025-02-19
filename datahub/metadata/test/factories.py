import uuid
from datetime import timezone

from random import randrange, sample

import factory
from faker import Faker

from datahub.core import constants
from datahub.metadata.models import Service

fake = Faker(locale='en_GB')


class ServiceFactory(factory.django.DjangoModelFactory):
    """Service factory."""

    segment = factory.Sequence(lambda n: f'name {n}')

    contexts = factory.LazyFunction(
        lambda: sample(
            Service.Context.values,
            randrange(0, len(Service.Context.values)),
        ),
    )

    class Meta:
        model = 'metadata.Service'


class ChildServiceFactory(factory.django.DjangoModelFactory):
    """Child service factory."""

    segment = factory.Sequence(lambda n: f'child name {n}')
    parent = factory.SubFactory(ServiceFactory)
    contexts = factory.LazyFunction(
        lambda: sample(
            Service.Context.values,
            randrange(0, len(Service.Context.values)),
        ),
    )

    class Meta:
        model = 'metadata.Service'


class TeamRoleFactory(factory.django.DjangoModelFactory):
    """TeamRole factory."""

    name = factory.Sequence(lambda n: f'name {n}')

    class Meta:
        model = 'metadata.TeamRole'


class TeamFactory(factory.django.DjangoModelFactory):
    """Team factory."""

    name = factory.Sequence(lambda n: f'name {n}')
    role = factory.SubFactory(TeamRoleFactory)
    uk_region_id = constants.UKRegion.east_midlands.value.id
    country_id = constants.Country.france.value.id
    tags = []

    class Meta:
        model = 'metadata.Team'


class ReferralSourceActivityFactory(factory.django.DjangoModelFactory):
    """ReferralSourceActivity factory."""

    name = factory.Sequence(lambda n: f'name {n}')

    class Meta:
        model = 'metadata.ReferralSourceActivity'


class ReferralSourceWebsiteFactory(factory.django.DjangoModelFactory):
    """ReferralSourceWebsite factory."""

    name = factory.Sequence(lambda n: f'name {n}')

    class Meta:
        model = 'metadata.ReferralSourceWebsite'


class ReferralSourceMarketingFactory(factory.django.DjangoModelFactory):
    """ReferralSourceMarketing factory."""

    name = factory.Sequence(lambda n: f'name {n}')

    class Meta:
        model = 'metadata.ReferralSourceMarketing'


class SectorClusterFactory(factory.django.DjangoModelFactory):
    """SectorCluster factory."""

    name = factory.Sequence(lambda n: f'name {n}')

    class Meta:
        model = 'metadata.SectorCluster'


class SectorFactory(factory.django.DjangoModelFactory):
    """Sector factory."""

    segment = factory.Sequence(lambda n: f'name {n}')

    class Meta:
        model = 'metadata.Sector'


class CountryFactory(factory.django.DjangoModelFactory):
    """Country factory."""

    class Meta:
        model = 'metadata.Country'


class AdministrativeAreasFactory(factory.django.DjangoModelFactory):
    """Administrative Area factory."""

    country = factory.SubFactory(CountryFactory)

    class Meta:
        model = 'metadata.AdministrativeArea'


class PostcodeDataFactory(factory.django.DjangoModelFactory):
    """Postcode data factory"""

    postcode = factory.Faker('postcode')
    modified_on = '2025-10-08T08:06:53+00:00'
    postcode_region = factory.Faker('postcode_region')
    publication_date = '2025-02-02T08:08:52+00:00'

    class Meta:
        model = 'metadata.PostcodeData'


def postcode_data_record_faker(overrides: dict | None = None) -> dict:
    data = {
        'id': str(uuid.uuid4()),
        'postcode': fake.postcode(),
        'modified_on': fake.date_time_between(
            start_date='-1y', tzinfo=timezone.utc,
        ),
        'publication_date': fake.date_time_between(
            start_date='-1y', tzinfo=timezone.utc,
        ),
        'postcode_region': constants.UKRegion.london.name,
    }
    if overrides:
        data.update(overrides)
    return data
