from functools import lru_cache
from importlib import import_module

from django.apps import AppConfig
from django.conf import settings

from .models import DataSet


SEARCH_APPS = [
    'datahub.search.companieshousecompany.CompaniesHouseCompanySearchApp',
    'datahub.search.company.CompanySearchApp',
    'datahub.search.contact.ContactSearchApp',
    'datahub.search.event.EventSearchApp',
    'datahub.search.investment.InvestmentSearchApp',
    'datahub.search.interaction.InteractionSearchApp',
    'datahub.search.omis.OrderSearchApp',
]


EXCLUDE_ALL = object()


class SearchApp:
    """Used to configure ES search modules to be used within Data Hub."""

    name = None
    es_model = None
    view = None
    export_view = None
    queryset = None
    permission_required = None

    def __init__(self, mod):
        """Create this search app without initialising any ES config."""
        self.mod = mod
        self.mod_signals = f'{self.mod}.signals'

    def init_es(self):
        """
        Makes sure mappings exist in Elasticsearch.
        This call is idempotent.
        """
        self.es_model.init(index=settings.ES_INDEX)

    def connect_signals(self):
        """
        Connects all signal handlers so DB models can be synced with Elasticsearch on save.
        """
        signals_mod = import_module(self.mod_signals)
        for receiver in signals_mod.receivers:
            receiver.connect()

    def disconnect_signals(self):
        """Disconnects all signal handlers."""
        signals_mod = import_module(self.mod_signals)
        for receiver in signals_mod.receivers:
            receiver.disconnect()

    def get_queryset(self):
        """Gets the queryset that will be synced with Elasticsearch."""
        return self.queryset.order_by('pk')

    def get_dataset(self):
        """Returns dataset that will be synchronised with Elasticsearch."""
        queryset = self.get_queryset()

        return DataSet(queryset, self.es_model)

    def get_permission_filters(self, request):
        """
        Gets filter arguments used to enforce permissions.

        The returned dict contains rules in the form of field names and values. Results must
        match at least one of these rules.

        Can also return EXCLUDE_ALL when no results should be returned.
        """
        return None


@lru_cache(maxsize=None)
def get_search_apps():
    """Registers all search apps specified in `SEARCH_APPS`."""
    return tuple(get_search_app(cls_path) for cls_path in SEARCH_APPS)


@lru_cache(maxsize=None)
def get_search_app(cls_path):
    """Registers a single search app."""
    mod_path, _, cls_name = cls_path.rpartition('.')
    mod = import_module(mod_path)
    cls = getattr(mod, cls_name)
    return cls(mod_path)


class SearchConfig(AppConfig):
    """Configures Elasticsearch connection when ready."""

    name = 'datahub.search'
    verbose_name = 'Search'

    def ready(self):
        """Configures Elasticsearch default connection."""
        from datahub.search.elasticsearch import configure_connection

        configure_connection()
        for app in get_search_apps():
            app.connect_signals()
