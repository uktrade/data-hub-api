from importlib import import_module

from django.apps import AppConfig
from django.conf import settings

from datahub.search import elasticsearch


SEARCH_APPS = [
    'datahub.search.company.CompanySearchApp',
    'datahub.search.contact.ContactSearchApp',
    'datahub.search.investment.InvestmentSearchApp',
]


class SearchApp:
    """Used to configure ES search modules to be used within Data Hub."""

    name = None
    ESModel = None

    def __init__(self, mod):
        """Initialise all ES components needed for the search."""
        self.mod = mod

        self.init_es()
        self.init_signals()

    def init_es(self):
        """
        Makes sure mappings exist in Elasticsearch.
        This call is idempotent.
        """
        self.ESModel.init(index=settings.ES_INDEX)

    def init_signals(self):
        """
        Imports all post_save signal handlers
        so DB models can be synced with Elasticsearch on save.
        """
        import_module(f'{self.mod}.signals')


class SearchConfig(AppConfig):
    """Configures Elasticsearch connection when ready."""

    name = 'datahub.search'
    verbose_name = 'Search'

    def __init__(self, *args, **kwargs):
        """Initialises this AppConfig"""
        super().__init__(*args, **kwargs)
        self.search_apps = {}

    def _register_search_apps(self):
        """Registers all search apps specified in `SEARCH_APPS`."""
        for search_mod in SEARCH_APPS:
            mod_path, _, cls_name = search_mod.rpartition('.')
            mod = import_module(mod_path)
            SearchClass = getattr(mod, cls_name)  # noqa: N806

            app = SearchClass(mod_path)
            self.search_apps[app.name] = app

    def ready(self):
        """Configures Elasticsearch default connection."""
        elasticsearch.configure_connection()
        elasticsearch.configure_index(settings.ES_INDEX)

        self._register_search_apps()
