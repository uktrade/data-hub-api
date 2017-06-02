from django.apps import AppConfig

from .elasticsearch import configure_connection


class SearchConfig(AppConfig):
    """Configures Elasticsearch connection when ready."""

    name = 'datahub.search'
    verbose_name = 'Search'

    def ready(self):
        """Configures Elasticsearch default connection."""
        configure_connection()
