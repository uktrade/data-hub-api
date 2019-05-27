import uuid
from random import randrange, sample

import factory

from datahub.core import constants
from datahub.metadata.models import Service


class ServiceFactory(factory.django.DjangoModelFactory):
    """Service factory."""

    id = factory.LazyFunction(uuid.uuid4)
    name = factory.Sequence(lambda n: f'name {n}')
    contexts = factory.LazyFunction(
        lambda: sample(
            Service.CONTEXTS._db_values,
            randrange(0, len(Service.CONTEXTS._db_values)),
        ),
    )

    class Meta:
        model = 'metadata.Service'


class TeamRoleFactory(factory.django.DjangoModelFactory):
    """TeamRole factory."""

    id = factory.LazyFunction(uuid.uuid4)
    name = factory.Sequence(lambda n: f'name {n}')

    class Meta:
        model = 'metadata.TeamRole'


class TeamFactory(factory.django.DjangoModelFactory):
    """Team factory."""

    id = factory.LazyFunction(uuid.uuid4)
    name = factory.Sequence(lambda n: f'name {n}')
    role = factory.SubFactory(TeamRoleFactory)
    uk_region_id = constants.UKRegion.east_midlands.value.id
    country_id = constants.Country.france.value.id
    tags = []

    class Meta:
        model = 'metadata.Team'


class ReferralSourceActivityFactory(factory.django.DjangoModelFactory):
    """ReferralSourceActivity factory."""

    id = factory.LazyFunction(uuid.uuid4)
    name = factory.Sequence(lambda n: f'name {n}')

    class Meta:
        model = 'metadata.ReferralSourceActivity'


class ReferralSourceWebsiteFactory(factory.django.DjangoModelFactory):
    """ReferralSourceWebsite factory."""

    id = factory.LazyFunction(uuid.uuid4)
    name = factory.Sequence(lambda n: f'name {n}')

    class Meta:
        model = 'metadata.ReferralSourceWebsite'


class ReferralSourceMarketingFactory(factory.django.DjangoModelFactory):
    """ReferralSourceMarketing factory."""

    id = factory.LazyFunction(uuid.uuid4)
    name = factory.Sequence(lambda n: f'name {n}')

    class Meta:
        model = 'metadata.ReferralSourceMarketing'


class SectorFactory(factory.django.DjangoModelFactory):
    """Sector factory."""

    id = factory.LazyFunction(uuid.uuid4)
    segment = factory.Sequence(lambda n: f'name {n}')

    class Meta:
        model = 'metadata.Sector'
