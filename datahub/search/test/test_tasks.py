from unittest.mock import Mock

import pytest

from datahub.search.apps import get_search_apps
from datahub.search.tasks import migrate_model, sync_all_models, sync_model
from datahub.search.test.utils import create_mock_search_app


def test_sync_model(monkeypatch):
    """Test that the sync_model task starts an ES sync for that model."""
    get_search_app_mock = Mock()
    monkeypatch.setattr('datahub.search.tasks.get_search_app', get_search_app_mock)

    sync_app_mock = Mock()
    monkeypatch.setattr('datahub.search.tasks.sync_app', sync_app_mock)

    search_app = next(iter(get_search_apps()))
    sync_model.apply(args=(search_app.name,))

    get_search_app_mock.assert_called_once_with(search_app.name)
    sync_app_mock.assert_called_once_with(get_search_app_mock.return_value)


def test_sync_all_models(monkeypatch):
    """Test that the sync_all_models task starts sub-tasks to sync all models."""
    sync_model_mock = Mock()
    monkeypatch.setattr('datahub.search.tasks.sync_model', sync_model_mock)

    sync_all_models.apply()
    tasks_created = {call[1]['args'][0] for call in sync_model_mock.apply_async.call_args_list}
    assert tasks_created == {app.name for app in get_search_apps()}


@pytest.mark.django_db
def test_migrate_model(monkeypatch):
    """Test that the migrate_model task calls resync_after_migrate()."""
    resync_after_migrate_mock = Mock()
    monkeypatch.setattr('datahub.search.tasks.resync_after_migrate', resync_after_migrate_mock)
    mock_app = create_mock_search_app(
        current_mapping_hash='current-hash',
        target_mapping_hash='target-hash',
    )
    get_search_app_mock = Mock(return_value=mock_app)
    monkeypatch.setattr('datahub.search.tasks.get_search_app', get_search_app_mock)

    migrate_model.apply(args=('test-app', 'target-hash'))
    resync_after_migrate_mock.assert_called_once_with(mock_app)


class MockRetryError(Exception):
    """Mock exception used to test retry behaviour."""


@pytest.mark.django_db
def test_migrate_model_with_mapping_hash_mismatch(monkeypatch):
    """
    Test that the migrate_model task calls self.retry() when the target mapping hash is not the
    expected one.

    This is to catch cases where the migrate_model task is received by an old app instance.
    """
    resync_after_migrate_mock = Mock()
    monkeypatch.setattr('datahub.search.tasks.resync_after_migrate', resync_after_migrate_mock)
    mock_app = create_mock_search_app(
        current_mapping_hash='current-hash',
        target_mapping_hash='target-hash',
    )
    get_search_app_mock = Mock(return_value=mock_app)
    monkeypatch.setattr('datahub.search.tasks.get_search_app', get_search_app_mock)
    retry_mock = Mock(side_effect=MockRetryError())
    monkeypatch.setattr(migrate_model, 'retry', retry_mock)

    res = migrate_model.apply(args=('test-app', 'another-hash'))

    with pytest.raises(MockRetryError):
        res.get()

    retry_mock.assert_called_once()

    resync_after_migrate_mock.assert_not_called()
