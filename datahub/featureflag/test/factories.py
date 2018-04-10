import uuid

import factory
from django.utils.timezone import now

from datahub.company.test.factories import AdviserFactory


class FeatureFlagFactory(factory.django.DjangoModelFactory):
    """Factory for creating a feature flag."""

    id = factory.LazyFunction(uuid.uuid4)
    name = factory.Faker('sentence', nb_words=4)
    description = factory.Faker('sentence', nb_words=8)

    created_on = now()
    created_by = factory.SubFactory(AdviserFactory)
    modified_by = factory.SubFactory(AdviserFactory)

    class Meta:
        model = 'featureflag.FeatureFlag'
