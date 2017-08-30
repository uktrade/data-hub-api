from django.apps import AppConfig


class MarketConfig(AppConfig):
    """Django App Config for the OMIS Market app."""

    name = 'datahub.omis.market'
    label = 'omis-market'  # namespaced app. Use this e.g. when migrating
