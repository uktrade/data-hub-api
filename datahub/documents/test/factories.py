from datetime import datetime
import uuid

import factory


class DocumentFactory(factory.django.DjangoModelFactory):
    """Document factory."""

    id = factory.Sequence(lambda _: str(uuid.uuid4()))
    path = factory.Sequence(lambda n: f'projects/doc{n}.txt')
    uploaded_on = factory.LazyFunction(datetime.now)

    class Meta:
        model = 'documents.Document'
