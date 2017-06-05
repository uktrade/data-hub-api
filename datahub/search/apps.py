from django.apps import AppConfig

from datahub.search import elasticsearch, models


class SearchConfig(AppConfig):
    """Configures Elasticsearch connection when ready."""

    name = 'datahub.search'
    verbose_name = 'Search'

    def ready(self):
        """Configures Elasticsearch default connection."""
        elasticsearch.configure_connection()

        # Makes sure mappings exist in Elasticsearch.
        # Those calls are idempotent
        models.Company.init(index=elasticsearch.ES_INDEX)
        models.Contact.init(index=elasticsearch.ES_INDEX)

        # Let's import Company and Contact post_save signal handlers
        # So DB models can be synced with Elasticsearch on save
        import datahub.search.signals # noqa
