from unittest.mock import Mock

from datahub.search.apps import SEARCH_APPS
from datahub.search.tasks import sync_all_models, sync_model


def test_sync_model(monkeypatch):
    """Test that the sync_model task starts an ES sync for that model."""
    get_search_app_mock = Mock()
    monkeypatch.setattr('datahub.search.tasks.get_search_app', get_search_app_mock)

    sync_dataset_mock = Mock()
    monkeypatch.setattr('datahub.search.tasks.sync_dataset', sync_dataset_mock)

    search_app_path = SEARCH_APPS[0]
    sync_model.apply(args=(search_app_path,))

    get_search_app_mock.assert_called_once_with(search_app_path)
    sync_dataset_mock.assert_called_once_with(
        get_search_app_mock.return_value.get_dataset.return_value
    )


def test_sync_all_models(monkeypatch):
    """Test that the sync_all_models task start sub-tasks to sync all models."""
    sync_model_mock = Mock()
    monkeypatch.setattr('datahub.search.tasks.sync_model', sync_model_mock)

    sync_all_models.apply()
    tasks_created = {call[1]['args'][0] for call in sync_model_mock.apply_async.call_args_list}
    assert tasks_created == frozenset(SEARCH_APPS)
