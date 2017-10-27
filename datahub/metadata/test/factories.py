import uuid

import factory

from datahub.core import constants


class ServiceFactory(factory.django.DjangoModelFactory):
    """Service factory."""

    id = factory.LazyFunction(uuid.uuid4)
    name = factory.Sequence(lambda n: f'name {n}')

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

    class Meta:
        model = 'metadata.Team'
