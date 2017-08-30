from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Django App Config for the OMIS Core app."""

    name = 'datahub.omis.core'
    label = 'omis-core'  # namespaced app. Use this e.g. when migrating
