from unittest.mock import Mock

import pytest
from django.test import override_settings

from datahub.search.sync_object import sync_object_async
from datahub.search.test.search_support.models import SimpleModel
from datahub.search.test.search_support.simplemodel import SimpleModelSearchApp


@pytest.mark.django_db
@pytest.mark.usefixtures('synchronous_thread_pool')
@override_settings(ENABLE_CELERY_ES_SYNC_OBJECT=False)
def test_sync_object_task_syncs_using_thread_pool(monkeypatch, setup_es):
    """Test that an object can be synced to Elasticsearch using the thread pool."""
    sync_object_task_mock = Mock()
    monkeypatch.setattr('datahub.search.sync_object.sync_object_task', sync_object_task_mock)

    obj = SimpleModel.objects.create()
    sync_object_async(SimpleModelSearchApp, obj.pk)
    setup_es.indices.refresh()

    assert setup_es.get(
        index=SimpleModelSearchApp.es_model.get_write_index(),
        doc_type=SimpleModelSearchApp.name,
        id=obj.pk,
    )
    sync_object_task_mock.apply_async.assert_not_called()


@pytest.mark.django_db
@override_settings(ENABLE_CELERY_ES_SYNC_OBJECT=True)
def test_sync_object_task_syncs_using_celery(monkeypatch, setup_es):
    """Test that an object can be synced to Elasticsearch using Celery."""
    submit_to_thread_pool_mock = Mock()
    monkeypatch.setattr(
        'datahub.search.sync_object.submit_to_thread_pool',
        submit_to_thread_pool_mock,
    )

    obj = SimpleModel.objects.create()
    sync_object_async(SimpleModelSearchApp, obj.pk)
    setup_es.indices.refresh()

    assert setup_es.get(
        index=SimpleModelSearchApp.es_model.get_write_index(),
        doc_type=SimpleModelSearchApp.name,
        id=obj.pk,
    )
    submit_to_thread_pool_mock.assert_not_called()
