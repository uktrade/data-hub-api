from django.apps import AppConfig


class QuoteConfig(AppConfig):
    """Django App Config for the Quote app."""

    name = 'datahub.omis.quote'
    label = 'omis-quote'  # namespaced app. Use this e.g. when migrating
