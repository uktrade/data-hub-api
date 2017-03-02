import uuid

import factory


class ServiceFactory(factory.django.DjangoModelFactory):
    """Service factory."""

    id = factory.Sequence(lambda x: '{0}'.format(uuid.uuid4()))
    name = factory.Sequence(lambda x: 'name {0}'.format(x))

    class Meta:
        model = 'metadata.Service'


class TeamFactory(factory.django.DjangoModelFactory):
    """Team factory."""

    id = factory.Sequence(lambda x: '{0}'.format(uuid.uuid4()))
    name = factory.Sequence(lambda x: 'name {0}'.format(x))

    class Meta:
        model = 'metadata.Team'
