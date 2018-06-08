from functools import lru_cache
from importlib import import_module

from django.apps import AppConfig

from datahub.search.elasticsearch import index_exists

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
    bulk_batch_size = 2000
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
        self.es_model.initialise_index()

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

    def get_permission_filters(self, request):
        """
        Gets filter arguments used to enforce permissions.

        The returned dict contains rules in the form of field names and values. Results must
        match at least one of these rules.

        Can also return EXCLUDE_ALL when no results should be returned.
        """
        return None


def get_search_apps():
    """Gets all registered search apps."""
    return tuple(_load_search_apps().values())


def get_search_apps_by_name(app_names=None):
    """
    Returns the apps for a particular set of app names.

    :param app_names: list of search app names to return app instances for, None for all
    """
    search_apps = get_search_apps()

    # if app_names empty, assume all apps
    return [
        search_app for search_app in search_apps
        if not app_names or search_app.name in app_names
    ]


def get_search_app(app_name):
    """Gets a single search app (by name)."""
    return _load_search_apps()[app_name]


def are_apps_initialised(apps):
    """Determines whether the given apps have been initialised (by init_es)."""
    return all(index_exists(app.es_model.get_write_alias()) for app in apps)


@lru_cache(maxsize=None)
def _load_search_apps():
    """Loads and registers all search apps specified in `SEARCH_APPS`."""
    apps = (_load_search_app(cls_path) for cls_path in SEARCH_APPS)
    return {app.name: app for app in apps}


@lru_cache(maxsize=None)
def _load_search_app(cls_path):
    """Loads and registers a single search app."""
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
