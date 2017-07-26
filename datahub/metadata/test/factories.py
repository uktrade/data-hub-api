import uuid

import factory

from datahub.core import constants


class EventFactory(factory.django.DjangoModelFactory):
    """Event factory."""

    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    name = factory.Sequence(lambda n: f'name {n}')

    class Meta:  # noqa: D101
        model = 'metadata.Event'


class ServiceFactory(factory.django.DjangoModelFactory):
    """Service factory."""

    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    name = factory.Sequence(lambda n: f'name {n}')

    class Meta:  # noqa: D101
        model = 'metadata.Service'


class TeamRoleFactory(factory.django.DjangoModelFactory):
    """TeamRole factory."""

    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    name = factory.Sequence(lambda n: f'name {n}')

    class Meta:  # noqa: D101
        model = 'metadata.TeamRole'


class TeamFactory(factory.django.DjangoModelFactory):
    """Team factory."""

    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    name = factory.Sequence(lambda n: f'name {n}')
    role = factory.SubFactory(TeamRoleFactory)
    uk_region_id = constants.UKRegion.east_midlands.value.id
    country_id = constants.Country.france.value.id

    class Meta:  # noqa: D101
        model = 'metadata.Team'
