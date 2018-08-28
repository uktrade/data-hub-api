import uuid

import factory

from ..models import EvidenceTag


class EvidenceTagFactory(factory.django.DjangoModelFactory):
    """Evidence tag factory."""

    id = factory.LazyFunction(uuid.uuid4)
    name = factory.Faker('sentence', nb_words=2)

    class Meta:
        model = EvidenceTag
