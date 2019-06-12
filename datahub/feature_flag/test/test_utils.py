from unittest.mock import Mock

import pytest
from django.http import Http404

from datahub.core.test.support.factories import PersonFactory
from datahub.core.test.support.models import Person
from datahub.feature_flag.test.factories import FeatureFlagFactory
from datahub.feature_flag.utils import (
    build_is_feature_flag_active_subquery,
    feature_flagged_view,
    is_feature_flag_active,
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


class TestBuildIsFeatureFlagActiveSubquery:
    """Tests for build_is_feature_flag_active_subquery()."""

    @pytest.mark.parametrize('is_active', (True, False))
    def test_annotation_equals_active_status_for_existent_feature_flag(self, is_active):
        """
        Test that the annotation value is same as the is_active value of a feature
        flag that exists.
        """
        code = 'test-flag'
        FeatureFlagFactory(code=code, is_active=is_active)
        PersonFactory()

        queryset = Person.objects.annotate(
            is_feature_flag_active=build_is_feature_flag_active_subquery(code),
        )
        assert queryset.first().is_feature_flag_active == is_active

    def test_annotation_is_false_for_non_existent_feature_flag(self):
        """Test that the annotation value is false with a non-existent feature flag."""
        code = 'test-flag'
        PersonFactory()

        queryset = Person.objects.annotate(
            is_feature_flag_active=build_is_feature_flag_active_subquery(code),
        )
        # Explicitly test for False as this reflects how it would be used when filtering a query
        # set
        assert queryset.first().is_feature_flag_active is False
