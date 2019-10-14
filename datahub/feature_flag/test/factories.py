import uuid

import factory
from django.utils.timezone import now

from datahub.company.test.factories import AdviserFactory


class FeatureFlagFactory(factory.django.DjangoModelFactory):
    """Factory for creating a feature flag."""

    id = factory.LazyFunction(uuid.uuid4)
    code = factory.Sequence(lambda n: f'CODE_{n}')
    description = factory.Faker('sentence', nb_words=8)
    is_active = True

    created_on = now()
    created_by = factory.SubFactory(AdviserFactory)
    modified_by = factory.SelfAttribute('created_by')

    class Meta:
        model = 'feature_flag.FeatureFlag'
