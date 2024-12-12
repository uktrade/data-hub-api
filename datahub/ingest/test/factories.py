from datetime import datetime

import factory

from datahub.ingest.constants import TEST_PREFIX


class IngestedObjectFactory(factory.django.DjangoModelFactory):
    """EYB Lead factory."""

    class Meta:
        model = 'ingest.IngestedObject'

    object_key = f'{TEST_PREFIX}/some/object/key.jsonl.gz'
    object_created = factory.LazyFunction(datetime.now)
