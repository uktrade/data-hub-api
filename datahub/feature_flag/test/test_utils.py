import pytest

from datahub.feature_flag.test.factories import FeatureFlagFactory
from datahub.feature_flag.utils import is_feature_flag_active

# mark the whole module for db use
pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    'code,is_active,lookup,expected',
    (
        ('test_flag', True, 'test_flag', True),
        ('test_flag', False, 'test_flag', False),
        ('', None, 'test_flag', False),
        ('test_flag', True, 'test', False),
    ),
)
def test_is_feature_flag(code, is_active, lookup, expected):
    """Tests if is_feature_flag returns correct state of feature flag."""
    if code != '':
        FeatureFlagFactory(code=code, is_active=is_active)

    result = is_feature_flag_active(lookup)
    assert result is expected
