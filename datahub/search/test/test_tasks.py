from unittest.mock import MagicMock, Mock

import pytest

from datahub.search.apps import get_search_apps
from datahub.search.sync_object import sync_object_async, sync_related_objects_async
from datahub.search.tasks import (
    complete_model_migration,
    sync_all_models,
    sync_model,
)
from datahub.search.test.search_support.models import RelatedModel, SimpleModel
from datahub.search.test.search_support.relatedmodel import RelatedModelSearchApp
from datahub.search.test.search_support.simplemodel import SimpleModelSearchApp
from datahub.search.test.utils import create_mock_search_app, doc_exists


def test_sync_model(monkeypatch):
    """Test that the sync_model task starts an OpenSearch sync for that model."""
    get_search_app_mock = Mock()
    monkeypatch.setattr('datahub.search.tasks.get_search_app', get_search_app_mock)

    sync_app_mock = Mock()
    monkeypatch.setattr('datahub.search.tasks.sync_app', sync_app_mock)

    search_app = next(iter(get_search_apps()))
    sync_model.apply_async(args=(search_app.name,))

    get_search_app_mock.assert_called_once_with(search_app.name)
    sync_app_mock.assert_called_once_with(get_search_app_mock.return_value)


def test_sync_all_models(monkeypatch):
    """Test that the sync_all_models task starts sub-tasks to sync all models."""
    sync_model_mock = Mock()
    monkeypatch.setattr('datahub.search.tasks.sync_model', sync_model_mock)

    sync_all_models.apply_async()
    tasks_created = {call[1]['args'][0] for call in sync_model_mock.apply_async.call_args_list}
    assert tasks_created == {app.name for app in get_search_apps()}


@pytest.mark.django_db
def test_sync_object_task_syncs(opensearch):
    """Test that the object task syncs an object to OpenSearch."""
    obj = SimpleModel.objects.create()
    sync_object_async(SimpleModelSearchApp, obj.pk)
    opensearch.indices.refresh()

    assert doc_exists(opensearch, SimpleModelSearchApp, obj.pk)


@pytest.mark.parametrize(
    'related_obj_filter',
    (
        None,
        {'simpleton__name': 'hello'},
    ),
)
@pytest.mark.django_db
def test_sync_related_objects_task_syncs(related_obj_filter, opensearch):
    """Test that related objects are synced to OpenSearch."""
    simpleton = SimpleModel.objects.create(name='hello')
    relation_1 = RelatedModel.objects.create(simpleton=simpleton)
    relation_2 = RelatedModel.objects.create(simpleton=simpleton)
    unrelated_obj = RelatedModel.objects.create()

    sync_related_objects_async(
        simpleton,
        'relatedmodel_set',
        related_obj_filter,
    )
    opensearch.indices.refresh()

    assert doc_exists(opensearch, RelatedModelSearchApp, relation_1.pk)
    assert doc_exists(opensearch, RelatedModelSearchApp, relation_2.pk)
    assert not doc_exists(opensearch, RelatedModelSearchApp, unrelated_obj.pk)


@pytest.mark.django_db
def test_complete_model_migration(monkeypatch):
    """Test that the complete_model_migration task calls resync_after_migrate()."""
    resync_after_migrate_mock = Mock()
    monkeypatch.setattr('datahub.search.tasks.resync_after_migrate', resync_after_migrate_mock)
    mock_app = create_mock_search_app(
        current_mapping_hash='current-hash',
        target_mapping_hash='target-hash',
    )
    get_search_app_mock = Mock(return_value=mock_app)
    monkeypatch.setattr('datahub.search.tasks.get_search_app', get_search_app_mock)

    complete_model_migration.apply_async(args=('test-app', 'target-hash'))
    resync_after_migrate_mock.assert_called_once_with(mock_app)


@pytest.mark.django_db
def test_complete_model_migration_aborts_when_already_in_progress(monkeypatch):
    """
    Test that the complete_model_migration task aborts when the lock for the same search app is
    already held.
    """
    resync_after_migrate_mock = Mock()
    monkeypatch.setattr('datahub.search.tasks.resync_after_migrate', resync_after_migrate_mock)
    mock_app = create_mock_search_app(
        current_mapping_hash='current-hash',
        target_mapping_hash='target-hash',
    )
    get_search_app_mock = Mock(return_value=mock_app)
    monkeypatch.setattr('datahub.search.tasks.get_search_app', get_search_app_mock)

    # Have to mock rather than acquire the lock as locks are per connection (if the lock is
    # already held by the current connection, the current connection can still acquire it again).
    advisory_lock_mock = MagicMock()
    advisory_lock_mock.return_value.__enter__.return_value = False
    monkeypatch.setattr('datahub.search.tasks.advisory_lock', advisory_lock_mock)
    complete_model_migration.apply_async(args=('test-app', 'target-hash'))

    # resync_after_migrate_mock should not have been called as the task should've exited instead
    resync_after_migrate_mock.assert_not_called()


class MockRetryError(Exception):
    """Mock exception used to test retry behaviour."""


@pytest.mark.django_db
def test_complete_model_migration_with_mapping_hash_mismatch(monkeypatch):
    """
    Test that the complete_model_migration task calls self.retry() when the target mapping hash is
    not the expected one.

    This is to catch cases where the complete_model_migration task is received by an old app
    instance.
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
    monkeypatch.setattr(complete_model_migration, 'retry', retry_mock)

    res = complete_model_migration.apply_async(args=('test-app', 'another-hash'))

    with pytest.raises(MockRetryError):
        res.get()

    retry_mock.assert_called_once()

    resync_after_migrate_mock.assert_not_called()
