import factory
from django.utils.timezone import now

from datahub.company.test.factories import AdviserFactory


class BaseFeatureFlagFactory(factory.django.DjangoModelFactory):
    """Base Factory for creating a feature flag."""

    code = factory.Sequence(lambda n: f'CODE_{n}')
    description = factory.Faker('sentence', nb_words=8)
    is_active = True

    created_on = now()
    created_by = factory.SubFactory(AdviserFactory)
    modified_by = factory.SelfAttribute('created_by')


class FeatureFlagFactory(BaseFeatureFlagFactory):
    """Factory for creating a feature flag."""

    class Meta:
        model = 'feature_flag.FeatureFlag'


class UserFeatureFlagFactory(BaseFeatureFlagFactory):
    """Factory for creating a user feature flag."""

    class Meta:
        model = 'feature_flag.UserFeatureFlag'
