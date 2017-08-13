from django.apps import AppConfig
from django.conf import settings

from datahub.search import elasticsearch


class SearchConfig(AppConfig):
    """Configures Elasticsearch connection when ready."""

    name = 'datahub.search'
    verbose_name = 'Search'

    def ready(self):
        """Configures Elasticsearch default connection."""
        from .company.models import Company
        from .contact.models import Contact
        from .investment.models import InvestmentProject

        elasticsearch.configure_connection()
        elasticsearch.configure_index(settings.ES_INDEX)

        # Makes sure mappings exist in Elasticsearch.
        # Those calls are idempotent
        Company.init(index=settings.ES_INDEX)
        Contact.init(index=settings.ES_INDEX)
        InvestmentProject.init(index=settings.ES_INDEX)

        # Let's import all post_save signal handlers
        # So DB models can be synced with Elasticsearch on save
        import datahub.search.company.signals  # noqa
        import datahub.search.contact.signals  # noqa
        import datahub.search.investment.signals  # noqa
