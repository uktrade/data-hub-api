import uuid
from datetime import datetime

import factory

from datahub.company.test.factories import AdviserFactory


class DocumentFactory(factory.django.DjangoModelFactory):
    """Document factory."""

    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    created_by = factory.SubFactory(AdviserFactory)
    modified_by = factory.SubFactory(AdviserFactory)
    path = factory.Sequence(lambda n: f'projects/doc{n}.txt')
    uploaded_on = factory.LazyFunction(datetime.now)

    class Meta:  # noqa: D101
        model = 'documents.Document'
