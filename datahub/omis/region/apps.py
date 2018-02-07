from django.apps import AppConfig


class RegionConfig(AppConfig):
    """Django App Config for the OMIS Region app."""

    name = 'datahub.omis.region'
    label = 'omis-region'  # namespaced app. Use this e.g. when migrating
