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


@mock.patch('datahub.search.management.commands.sync_es.sync_es')
@mock.patch('datahub.search.management.commands.sync_es.get_search_apps_by_name')
@mock.patch(
    'datahub.search.apps.index_exists',
    mock.Mock(return_value=True),
)
@pytest.mark.django_db
def test_sync_es(get_search_apps_by_name_mock, sync_es_mock):
    """Tests syncing app to Elasticsearch."""
    management.call_command(sync_es.Command(), batch_size=1)

    sync_es_mock.assert_called_once_with(
        batch_size=1,
        search_apps=get_search_apps_by_name_mock.return_value,
    )


@pytest.mark.parametrize(
    'search_model',
    (app.name for app in get_search_apps()),
)
@mock.patch('datahub.search.management.commands.sync_es.sync_app')
@mock.patch(
    'datahub.search.apps.index_exists',
    mock.Mock(return_value=True),
)
def test_sync_one_model(sync_app_mock, search_model):
    """
    Test that --model can be used to specify what we weant to sync.
    """
    management.call_command(sync_es.Command(), model=[search_model])

    assert sync_app_mock.call_count == 1


@mock.patch('datahub.search.management.commands.sync_es.sync_app')
@mock.patch(
    'datahub.search.apps.index_exists',
    mock.Mock(return_value=True),
)
def test_sync_all_models(sync_app_mock):
    """
    Test that if --model is not used, all the search apps are synced.
    """
    management.call_command(sync_es.Command())

    assert sync_app_mock.call_count == len(get_search_apps())


@mock.patch('datahub.search.management.commands.sync_es.sync_app')
@mock.patch(
    'datahub.search.apps.index_exists',
    mock.Mock(return_value=True),
)
def test_sync_invalid_model(sync_app_mock):
    """
    Test that if an invalid value is used with --model, nothing gets synced.
    """
    management.call_command(sync_es.Command(), model='invalid')

    assert sync_app_mock.call_count == 0
