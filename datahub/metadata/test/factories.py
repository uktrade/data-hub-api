import uuid

import factory


class EventFactory(factory.django.DjangoModelFactory):
    """Event factory."""

    id = factory.Sequence(lambda _: str(uuid.uuid4()))
    name = factory.Sequence(lambda n: f'name {n}')

    class Meta:
        model = 'metadata.Event'


class ServiceFactory(factory.django.DjangoModelFactory):
    """Service factory."""

    id = factory.Sequence(lambda _: str(uuid.uuid4()))
    name = factory.Sequence(lambda n: f'name {n}')

    class Meta:
        model = 'metadata.Service'


class TeamFactory(factory.django.DjangoModelFactory):
    """Team factory."""

    id = factory.Sequence(lambda _: str(uuid.uuid4()))
    name = factory.Sequence(lambda n: 'name {n}')

    class Meta:
        model = 'metadata.Team'
