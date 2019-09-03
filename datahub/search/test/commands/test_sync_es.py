from unittest import mock

import pytest
from django.core import management
from django.core.management.base import CommandError

from datahub.search.apps import get_search_apps
from datahub.search.management.commands import sync_es


@mock.patch(
    'datahub.search.apps.index_exists',
    mock.Mock(return_value=False),
)
def test_fails_if_index_doesnt_exist():
    """Tests that if the index doesn't exist, sync_es fails."""
    with pytest.raises(CommandError):
        management.call_command(sync_es.Command())


@pytest.mark.parametrize(
    'search_model',
    (app.name for app in get_search_apps()),
)
@mock.patch('datahub.search.management.commands.sync_es.sync_model')
@mock.patch(
    'datahub.search.apps.index_exists',
    mock.Mock(return_value=True),
)
def test_sync_one_model(sync_model_mock, search_model):
    """
    Test that --model can be used to specify what we want to sync.
    """
    management.call_command(sync_es.Command(), model=[search_model])

    assert sync_model_mock.apply.call_count == 1


@mock.patch('datahub.search.management.commands.sync_es.sync_model')
@mock.patch(
    'datahub.search.apps.index_exists',
    mock.Mock(return_value=True),
)
def test_sync_all_models(sync_model_mock):
    """
    Test that if --model is not used, all the search apps are synced.
    """
    management.call_command(sync_es.Command())

    assert sync_model_mock.apply.call_count == len(get_search_apps())


@mock.patch('datahub.search.management.commands.sync_es.sync_model')
@mock.patch(
    'datahub.search.apps.index_exists',
    mock.Mock(return_value=True),
)
def test_sync_invalid_model(sync_model_mock):
    """
    Test that if an invalid value is used with --model, nothing gets synced.
    """
    management.call_command(sync_es.Command(), model='invalid')

    assert sync_model_mock.apply.call_count == 0
