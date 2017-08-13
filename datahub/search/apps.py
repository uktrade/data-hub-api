from functools import lru_cache
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
    plural_name = None
    ESModel = None
    view = None

    def __init__(self, mod):
        """Create this search app without initialising any ES config."""
        self.mod = mod

    def init_all(self):
        """Initialise all ES configs."""
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


@lru_cache(maxsize=None)
def get_search_apps():
    """Registers all search apps specified in `SEARCH_APPS`."""
    search_apps = []

    for search_mod in SEARCH_APPS:
        mod_path, _, cls_name = search_mod.rpartition('.')
        mod = import_module(mod_path)
        SearchClass = getattr(mod, cls_name)  # noqa: N806

        app = SearchClass(mod_path)
        search_apps.append(app)

    return search_apps


class SearchConfig(AppConfig):
    """Configures Elasticsearch connection when ready."""

    name = 'datahub.search'
    verbose_name = 'Search'

    def __init__(self, *args, **kwargs):
        """Initialises this AppConfig"""
        super().__init__(*args, **kwargs)
        self.search_apps = {}

    def ready(self):
        """Configures Elasticsearch default connection."""
        elasticsearch.configure_connection()
        elasticsearch.configure_index(settings.ES_INDEX)

        for search_app in get_search_apps():
            search_app.init_all()
