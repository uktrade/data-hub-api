from django.apps import AppConfig


class FeatureFlagConfig(AppConfig):
    """Django App Config for the feature flag app."""

    name = 'datahub.feature_flag'
    verbose_name = 'Feature Flag'
