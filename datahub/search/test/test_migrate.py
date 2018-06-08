from unittest.mock import Mock

import pytest

from datahub.core.exceptions import DataHubException
from datahub.search.apps import get_search_apps
from datahub.search.migrate import migrate_app, migrate_apps
from datahub.search.test.utils import create_mock_search_app


def test_migrate_apps(monkeypatch):
    """Test that migrate_apps() migrates the correct apps."""
    migrate_app_mock = Mock()
    monkeypatch.setattr('datahub.search.migrate.migrate_app', migrate_app_mock)
    apps = {app.name for app in list(get_search_apps())[:2]}
    migrate_apps(apps)
    assert {args[0][0] for args in migrate_app_mock.call_args_list} == apps


def test_migrate_app_with_app_needing_migration(monkeypatch, mock_es_client):
    """Test that migrate_app() migrates an app needing migration."""
    migrate_model_task_mock = Mock()
    monkeypatch.setattr('datahub.search.migrate.migrate_model', migrate_model_task_mock)

    mock_client = mock_es_client.return_value
    old_index = 'test-index'
    new_index = 'test-index-target-hash'
    current_hash = 'current-hash'
    target_hash = 'target-hash'
    mock_app = create_mock_search_app(current_hash, target_hash, write_index=old_index)

    migrate_app(mock_app)

    mock_app.es_model.create_index.assert_called_once_with(new_index)

    mock_client.indices.update_aliases.assert_called_once_with(
        body={
            'actions': [
                {
                    'add': {
                        'alias': 'test-read-alias',
                        'indices': [new_index]
                    }
                },
                {
                    'add': {
                        'alias': 'test-write-alias',
                        'indices': [new_index]
                    }
                },
                {
                    'remove': {
                        'alias': 'test-write-alias',
                        'indices': [old_index]
                    }
                },
            ]
        }
    )

    migrate_model_task_mock.apply_async.assert_called_once_with(
        args=(mock_app.name, target_hash)
    )


def test_migrate_app_with_app_not_needing_migration(monkeypatch, mock_es_client):
    """Test that migrate_app() migrates an app needing migration."""
    migrate_model_task_mock = Mock()
    monkeypatch.setattr('datahub.search.migrate.migrate_model', migrate_model_task_mock)

    mock_client = mock_es_client.return_value
    old_index = 'test-index-current-hash'
    current_hash = 'current-hash'
    target_hash = 'current-hash'
    mock_app = create_mock_search_app(current_hash, target_hash, write_index=old_index)

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
    monkeypatch.setattr('datahub.search.migrate.migrate_model', migrate_model_task_mock)

    mock_client = mock_es_client.return_value
    old_index = 'test-index-current-hash'
    read_indices = ('test-index-current-hash', 'another-index')
    current_hash = 'current-hash'
    target_hash = 'current-hash'
    mock_app = create_mock_search_app(
        current_hash,
        target_hash,
        read_indices=read_indices,
        write_index=old_index,
    )

    migrate_app(mock_app)

    mock_app.es_model.create_index.assert_not_called()
    mock_client.indices.update_aliases.assert_not_called()

    migrate_model_task_mock.apply_async.assert_called_once_with(
        args=(mock_app.name, target_hash)
    )


def test_migrate_app_with_app_in_invalid_state(monkeypatch, mock_es_client):
    """
    Test that migrate_app() raises an exception for apps in an invalid state.

    This refers to an app that needs migrating, but the current write index is not one of
    the read indices. This should never happen.
    """
    migrate_model_task_mock = Mock()
    monkeypatch.setattr('datahub.search.migrate.migrate_model', migrate_model_task_mock)

    read_indices = ('read-index',)
    write_index = 'write-index'
    current_hash = 'current-hash'
    target_hash = 'target-hash'
    mock_app = create_mock_search_app(
        current_hash,
        target_hash,
        read_indices=read_indices,
        write_index=write_index,
    )

    with pytest.raises(DataHubException):
        migrate_app(mock_app)

    migrate_model_task_mock.apply_async.assert_not_called()
