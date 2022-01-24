from unittest.mock import Mock

import pytest
from django.http import Http404

from datahub.company.test.factories import AdviserFactory
from datahub.feature_flag.test.factories import FeatureFlagFactory, UserFeatureFlagFactory
from datahub.feature_flag.utils import (
    feature_flagged_view,
    is_feature_flag_active,
    is_user_feature_flag_active,
)

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


class TestFeatureFlaggedView:
    """Test the feature_flagged_view decorator."""

    def test_raises_404_if_flag_does_not_exist(self):
        """Test that an Http404 is raised if the feature flag does not exist."""
        mock = Mock()
        with pytest.raises(Http404):
            feature_flagged_view('test-feature-flag')(mock)()
        mock.assert_not_called()

    def test_raises_404_is_flag_inactive(self):
        """Test that an Http404 is raised if the feature flag is inactive."""
        FeatureFlagFactory(code='test-feature-flag', is_active=False)

        mock = Mock()
        with pytest.raises(Http404):
            feature_flagged_view('test-feature-flag')(mock)()
        mock.assert_not_called()

    def test_calls_view_if_flag_active(self):
        """Test that the wrapped view is caleld if the feature flag is active."""
        FeatureFlagFactory(code='test-feature-flag', is_active=True)

        mock = Mock()
        feature_flagged_view('test-feature-flag')(mock)()
        mock.assert_called_once()


@pytest.mark.parametrize(
    'code,user,is_active,lookup,expected',
    (
        ('test_user_flag', 'flagged_user', True, 'test_user_flag', True),
        ('test_user_flag', 'unflagged_user', True, 'test_user_flag', False),
        ('test_user_flag', 'flagged_user', False, 'test_user_flag', False),
        ('test_user_flag', 'unflagged_user', False, 'test_user_flag', False),
        ('', 'unflagged_user', None, 'test_user_flag', False),
        ('test_user_flag', 'flagged_user', True, 'test', False),
        ('test_user_flag', 'unflagged_user', True, 'test', False),
    ),
)
def test_is_user_feature_flag(code, user, is_active, lookup, expected):
    """Tests if is_user_feature_flag returns correct state of feature flag."""
    if code != '':
        flag = UserFeatureFlagFactory(code=code, is_active=is_active)

    if user == 'flagged_user':
        advisor = AdviserFactory()
        advisor.features.set([flag])

    if user == 'unflagged_user':
        advisor = AdviserFactory()

    result = is_user_feature_flag_active(lookup, advisor)
    assert result is expected
