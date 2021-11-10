import pytest

from datahub.core.test_utils import create_test_user
from datahub.feature_flag.models import FeatureFlag
from datahub.search.apps import get_search_apps
from datahub.search.constants import FUZZY_SEARCH_FEATURE_FLAG
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


@pytest.fixture
def search_support_user():
    """A user with permissions for search_support views."""
    return create_test_user(permission_codenames=['view_simplemodel', 'view_relatedmodel'])


@pytest.fixture
def fuzzy_search_feature():
    """Enable the fuzzy search feature flag"""
    return FeatureFlag.objects.update_or_create(
        code=FUZZY_SEARCH_FEATURE_FLAG,
        defaults={'is_active': True},
    )
