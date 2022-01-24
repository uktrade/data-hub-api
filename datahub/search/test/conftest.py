from datahub.search.apps import get_search_apps
from datahub.search.views import v3_view_registry, v4_view_registry


def pytest_generate_tests(metafunc):
    """Parametrises tests that use the `search_app` or `search_view` fixture."""
    if 'search_app' in metafunc.fixturenames:
        apps = get_search_apps()
        metafunc.parametrize(
            'search_app',
            apps,
            ids=[app.__class__.__name__ for app in apps],
        )

    if 'search_view' in metafunc.fixturenames:
        views = [
            *v3_view_registry.values(),
            *v4_view_registry.values(),
        ]
        metafunc.parametrize(
            'search_view',
            views,
            ids=[view.__class__.__name__ for view in views],
        )
