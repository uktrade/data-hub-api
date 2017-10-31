import uuid

import factory
from django.utils.timezone import utc

from datahub.company.test.factories import AdviserFactory


class DocumentFactory(factory.django.DjangoModelFactory):
    """Document factory."""

    id = factory.LazyFunction(uuid.uuid4)
    created_by = factory.SubFactory(AdviserFactory)
    modified_by = factory.SubFactory(AdviserFactory)
    path = factory.Sequence(lambda n: f'projects/doc{n}.txt')
    uploaded_on = factory.Faker('past_datetime', tzinfo=utc)

    class Meta:
        model = 'documents.Document'
