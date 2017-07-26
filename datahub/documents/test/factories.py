import uuid
from datetime import datetime

import factory


class DocumentFactory(factory.django.DjangoModelFactory):
    """Document factory."""

    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    path = factory.Sequence(lambda n: f'projects/doc{n}.txt')
    uploaded_on = factory.LazyFunction(datetime.now)

    class Meta:  # noqa: D101
        model = 'documents.Document'
