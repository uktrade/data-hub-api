from uuid import uuid4

import factory


class MetadataModelFactory(factory.django.DjangoModelFactory):
    """MetadataModel factory."""

    id = factory.LazyFunction(uuid4)
    name = factory.Faker('sentence')

    class Meta:
        model = 'support.MetadataModel'
