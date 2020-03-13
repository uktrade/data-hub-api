from unittest import mock

import pytest

from datahub.search.apps import (
    get_search_app,
    get_search_app_by_model,
    get_search_app_by_search_model,
)
from datahub.search.test.search_support.simplemodel import SimpleModelSearchApp
from datahub.search.test.search_support.simplemodel.models import ESSimpleModel


@mock.patch('datahub.search.apps._load_search_apps')
class TestGetSearchApp:
    """Tests related to `get_search_app`."""

    def test_found(self, mocked_load_search_apps):
        """
        Test that get_search_app returns the right search app for the name passed in.
        """
        search_app = mock.Mock()

        mocked_load_search_apps.return_value = {
            'app1': mock.Mock(),
            'app2': search_app,
        }
        assert get_search_app('app2') == search_app

    def test_not_found(self, mocked_load_search_apps):
        """
        Test that get_search_app raises KeyError if it can't find the right
        search app for the name passed in.
        """
        mocked_load_search_apps.return_value = {
            'app1': mock.Mock(),
        }
        with pytest.raises(KeyError):
            get_search_app(mock.Mock())


@mock.patch('datahub.search.apps._load_search_apps')
class TestGetSearchAppByModel:
    """Tests related to `get_search_app_by_model`."""

    def test_found(self, mocked_load_search_apps):
        """
        Test that get_search_app_by_model returns the right
        search app for the model passed in.
        """
        model = mock.Mock()
        search_app = mock.Mock(queryset=mock.Mock(model=model))

        mocked_load_search_apps.return_value = {
            'app1': mock.Mock(),
            'app2': search_app,
        }
        assert get_search_app_by_model(model) == search_app

    def test_not_found(self, mocked_load_search_apps):
        """
        Test that get_search_app_by_model raises LookupError if it
        can't find the right search app for the model passed in.
        """
        mocked_load_search_apps.return_value = {
            'app1': mock.Mock(),
        }
        with pytest.raises(LookupError):
            get_search_app_by_model(mock.Mock())


class TestGetSearchAppBySearchModel:
    """Tests for `get_search_app_by_search_model`."""

    def test_found(self):
        """Test that the expected app is returned for a registered search model."""
        assert get_search_app_by_search_model(ESSimpleModel) is SimpleModelSearchApp

    def test_not_found(self):
        """
        Test that get_search_app_by_model raises LookupError if it
        can't find the right search app for the search model passed in.
        """
        with pytest.raises(LookupError):
            get_search_app_by_model(mock.Mock())
