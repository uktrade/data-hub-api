from functools import lru_cache
from importlib import import_module

from django.apps import AppConfig
from django.conf import settings

from datahub.search.elasticsearch import configure_connection, index_exists

EXCLUDE_ALL = object()


class SearchApp:
    """Used to configure ES search modules to be used within Data Hub."""

    name = None
    es_model = None
    bulk_batch_size = 2000

    queryset = None
    exclude_from_global_search = False
    # A sequence of permissions. The user must have one of these permissions to perform searches.
    view_permissions = None
    # A single permission. The user must have this permission and a permission in view_permissions
    # in order to export search results.
    export_permission = None

    @classmethod
    def load_views(cls):
        """Loads the views submodule for the app to ensure views are registered."""
        cls._load_submodule('views')

    @classmethod
    def get_signal_receivers(cls):
        """Returns the signal receivers for this search app."""
        return cls._load_submodule('signals').receivers

    @classmethod
    def connect_signals(cls):
        """
        Connects all signal handlers so DB models can be synced with Elasticsearch on save.
        """
        for receiver in cls.get_signal_receivers():
            receiver.connect()

    @classmethod
    def disconnect_signals(cls):
        """Disconnects all signal handlers."""
        for receiver in cls.get_signal_receivers():
            receiver.disconnect()

    @classmethod
    def get_permission_filters(cls, request):
        """
        Gets filter arguments used to enforce permissions.

        The returned dict contains rules in the form of field names and values. Results must
        match at least one of these rules.

        Can also return EXCLUDE_ALL when no results should be returned.
        """
        return None

    @classmethod
    def _load_submodule(cls, name):
        package, _, _ = cls.__module__.rpartition('.')
        module = f'{package}.{name}'
        return import_module(module)


def get_search_apps():
    """Gets all registered search apps."""
    return tuple(_load_search_apps().values())


def get_search_apps_by_name(app_names=None):
    """
    Returns the apps for a particular set of app names.

    :param app_names: list of search app names to return app instances for, falsey value for
                      all apps
    """
    search_apps = get_search_apps()

    return [
        search_app for search_app in search_apps
        if not app_names or search_app.name in app_names
    ]


def get_global_search_apps_as_mapping():
    """Gets all registered search apps that should be included in global (basic) search."""
    return {
        app_name: app
        for app_name, app in _load_search_apps().items()
        if not app.exclude_from_global_search
    }


def get_search_app(app_name):
    """Gets a single search app (by name)."""
    return _load_search_apps()[app_name]


def are_apps_initialised(apps):
    """Determines whether the given apps have been initialised (by migrate_es)."""
    return all(index_exists(app.es_model.get_write_alias()) for app in apps)


@lru_cache(maxsize=None)
def get_search_app_by_model(model):
    """
    :returns: a single search app (by django model)
    :param model: django model for the search app
    :raises LookupError: if it can't find the search app
    """
    for search_app in get_search_apps():
        if search_app.queryset.model is model:
            return search_app
    raise LookupError(f'search app for {model} not found.')


@lru_cache(maxsize=None)
def _load_search_apps():
    """Loads and registers all search apps specified in `SEARCH_APPS`."""
    apps = (_load_search_app(cls_path) for cls_path in settings.SEARCH_APPS)
    return {app.name: app for app in apps}


@lru_cache(maxsize=None)
def _load_search_app(cls_path):
    """Loads and registers a single search app."""
    mod_path, _, cls_name = cls_path.rpartition('.')
    mod = import_module(mod_path)
    return getattr(mod, cls_name)


class SearchConfig(AppConfig):
    """Configures Elasticsearch connection when ready."""

    name = 'datahub.search'
    verbose_name = 'Search'

    def ready(self):
        """
        Configures the default Elasticsearch connection, connects signal receivers and
        registers views.
        """
        # The automatic connection configuration is disabled during tests because the connection
        # is set up using different environment variables in the _es_client pytest fixture
        if settings.SEARCH_CONFIGURE_CONNECTION_ON_READY:
            configure_connection()

        for app in get_search_apps():
            # For tests we disable automatic connection of signal receivers on app ready.
            # They are instead only enabled for tests that use the es_with_signals pytest fixture
            if settings.SEARCH_CONNECT_SIGNAL_RECEIVERS_ON_READY:
                app.connect_signals()

            app.load_views()
