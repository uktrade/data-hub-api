from unittest.mock import ANY, call, Mock

import pytest
from django.conf import settings

from datahub.core.exceptions import DataHubException
from datahub.search.apps import _load_search_apps, get_search_apps, SearchApp
from datahub.search.migrate import migrate_app, migrate_apps
from datahub.search.models import BaseESModel, DEFAULT_MAPPING_TYPE
from datahub.search.test.utils import create_mock_search_app

SAMPLE_APP_NAME = 'sample'


class SampleModel(BaseESModel):
    """Sample (dummy) search model."""

    class Meta:
        doc_type = DEFAULT_MAPPING_TYPE

    class Index:
        doc_type = DEFAULT_MAPPING_TYPE


class SampleSearchApp(SearchApp):
    """Sample (dummy) search app."""

    name = SAMPLE_APP_NAME
    es_model = SampleModel


@pytest.fixture
def sample_search_app(settings):
    """Fixture that registers SampleSearchApp and yields it."""
    settings.SEARCH_APPS = [f'{SampleSearchApp.__module__}.{SampleSearchApp.__qualname__}']
    _load_search_apps.cache_clear()
    yield SampleSearchApp
    _load_search_apps.cache_clear()


def test_migrate_apps(monkeypatch):
    """Test that migrate_apps() migrates the correct apps."""
    migrate_app_mock = Mock()
    monkeypatch.setattr('datahub.search.migrate.migrate_app', migrate_app_mock)
    apps = {app.name for app in list(get_search_apps())[:2]}
    migrate_apps(apps)
    assert {args[0][0] for args in migrate_app_mock.call_args_list} == apps


def test_migrate_app_with_uninitialised_app(monkeypatch, mock_es_client, sample_search_app):
    """
    Test that migrate_app() creates an index and schedules an initial sync for an
    uninitialised search app.
    """
    sync_model_task_mock = Mock()
    monkeypatch.setattr('datahub.search.migrate.sync_model', sync_model_task_mock)
    mock_client = mock_es_client.return_value
    mock_client.indices.exists_alias.side_effect = [
        # No alias at first attempt
        False,
        # Return True once alias created
        True,
    ]

    migrate_app(sample_search_app)

    expected_index_name = (
        f'{settings.ES_INDEX_PREFIX}-{SAMPLE_APP_NAME}-091a1c3a42f7e9fb3ff69b49a7b45881'
    )
    assert mock_client.indices.create.call_args_list == [
        call(index=expected_index_name, body=ANY),
    ]
    assert sync_model_task_mock.apply_async.call_args_list == [
        call(args=(sample_search_app.name,)),
    ]


def test_migrate_app_with_app_needing_migration(monkeypatch, mock_es_client):
    """Test that migrate_app() migrates an app needing migration."""
    migrate_model_task_mock = Mock()
    monkeypatch.setattr('datahub.search.migrate.complete_model_migration', migrate_model_task_mock)
    create_index_mock = Mock()
    monkeypatch.setattr('datahub.search.migrate.create_index', create_index_mock)

    mock_client = mock_es_client.return_value
    old_index = 'test-index'
    new_index = 'test-index-target-hash'
    current_hash = 'current-hash'
    target_hash = 'target-hash'
    mock_app = create_mock_search_app(
        current_mapping_hash=current_hash,
        target_mapping_hash=target_hash,
        write_index=old_index,
    )

    migrate_app(mock_app)

    create_index_mock.assert_called_once_with(new_index, mock_app.es_model._doc_type.mapping)

    mock_client.indices.update_aliases.assert_called_once_with(
        body={
            'actions': [
                {
                    'add': {
                        'alias': 'test-read-alias',
                        'indices': [new_index],
                    },
                },
                {
                    'add': {
                        'alias': 'test-write-alias',
                        'indices': [new_index],
                    },
                },
                {
                    'remove': {
                        'alias': 'test-write-alias',
                        'indices': [old_index],
                    },
                },
            ],
        },
    )

    migrate_model_task_mock.apply_async.assert_called_once_with(
        args=(mock_app.name, target_hash),
    )


def test_migrate_app_with_app_not_needing_migration(monkeypatch, mock_es_client):
    """Test that migrate_app() migrates an app needing migration."""
    migrate_model_task_mock = Mock()
    monkeypatch.setattr('datahub.search.migrate.complete_model_migration', migrate_model_task_mock)

    mock_client = mock_es_client.return_value
    old_index = 'test-index-current-hash'
    current_hash = 'current-hash'
    target_hash = 'current-hash'
    mock_app = create_mock_search_app(
        current_mapping_hash=current_hash,
        target_mapping_hash=target_hash,
        write_index=old_index,
    )

    migrate_app(mock_app)

    mock_app.es_model.create_index.assert_not_called()
    mock_client.indices.update_aliases.assert_not_called()
    migrate_model_task_mock.apply_async.assert_not_called()


def test_migrate_app_with_app_in_inconsistent_state(monkeypatch, mock_es_client):
    """
    Test that migrate_app() resyncs an app in an inconsistent state.

    This refers to an app with multiple read indices (i.e. an app with an interrupted migration).

    In this case, a resync should be scheduled to attempt to complete the migration.
    """
    migrate_model_task_mock = Mock()
    monkeypatch.setattr('datahub.search.migrate.complete_model_migration', migrate_model_task_mock)

    mock_client = mock_es_client.return_value
    old_index = 'test-index-current-hash'
    read_indices = ('test-index-current-hash', 'another-index')
    current_hash = 'current-hash'
    target_hash = 'current-hash'
    mock_app = create_mock_search_app(
        current_mapping_hash=current_hash,
        target_mapping_hash=target_hash,
        read_indices=read_indices,
        write_index=old_index,
    )

    migrate_app(mock_app)

    mock_app.es_model.create_index.assert_not_called()
    mock_client.indices.update_aliases.assert_not_called()

    migrate_model_task_mock.apply_async.assert_called_once_with(
        args=(mock_app.name, target_hash),
    )


def test_migrate_app_with_app_in_invalid_state(monkeypatch, mock_es_client):
    """
    Test that migrate_app() raises an exception for apps in an invalid state.

    This refers to an app that needs migrating, but the current write index is not one of
    the read indices. This should never happen.
    """
    migrate_model_task_mock = Mock()
    monkeypatch.setattr('datahub.search.migrate.complete_model_migration', migrate_model_task_mock)

    read_indices = ('read-index',)
    write_index = 'write-index'
    current_hash = 'current-hash'
    target_hash = 'target-hash'
    mock_app = create_mock_search_app(
        current_mapping_hash=current_hash,
        target_mapping_hash=target_hash,
        read_indices=read_indices,
        write_index=write_index,
    )

    with pytest.raises(DataHubException):
        migrate_app(mock_app)

    migrate_model_task_mock.apply_async.assert_not_called()
