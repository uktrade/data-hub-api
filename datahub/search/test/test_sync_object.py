import pytest

from datahub.search.sync_object import sync_object, sync_object_async, sync_related_objects_async
from datahub.search.test.search_support.models import RelatedModel, SimpleModel
from datahub.search.test.search_support.relatedmodel import RelatedModelSearchApp
from datahub.search.test.search_support.simplemodel import SimpleModelSearchApp
from datahub.search.test.utils import doc_exists


@pytest.mark.django_db
def test_sync_object_task_syncs_using_rq(opensearch):
    """Test that an object can be synced to OpenSearch using RQ."""
    obj = SimpleModel.objects.create()
    sync_object_async(SimpleModelSearchApp, obj.pk)
    opensearch.indices.refresh()

    assert doc_exists(opensearch, SimpleModelSearchApp, obj.pk)


@pytest.mark.django_db
def test_sync_related_objects_syncs_using_rq(opensearch):
    """Test that related objects can be synced to OpenSearch using datahub queue."""
    simpleton = SimpleModel.objects.create()
    relation_1 = RelatedModel.objects.create(simpleton=simpleton)
    relation_2 = RelatedModel.objects.create(simpleton=simpleton)
    unrelated_obj = RelatedModel.objects.create()

    sync_related_objects_async(simpleton, 'relatedmodel_set')
    opensearch.indices.refresh()

    assert doc_exists(opensearch, RelatedModelSearchApp, relation_1.pk)
    assert doc_exists(opensearch, RelatedModelSearchApp, relation_2.pk)
    assert not doc_exists(opensearch, RelatedModelSearchApp, unrelated_obj.pk)


@pytest.mark.django_db
def test_sync_object_task_handles_obj_no_longer_in_db(opensearch, caplog):
    """Test that the sync does not crash trying to sync a deleted object, there are signals which
    can trigger the sync for deleted objects.
    """
    caplog.set_level('ERROR')
    obj = SimpleModel.objects.create()
    obj_id = obj.id

    obj.delete()
    sync_object(SimpleModelSearchApp, obj_id)
    opensearch.indices.refresh()

    assert not doc_exists(opensearch, SimpleModelSearchApp, obj_id)
    assert (
        f'An error occurred syncing a {SimpleModelSearchApp.name} object with id {obj_id}: '
        'SimpleModel matching query does not exist. '
        f'Object {SimpleModelSearchApp.name} may have been deleted before being synced'
        in caplog.text
    )

    sync_object_async(SimpleModelSearchApp, obj_id)
    opensearch.indices.refresh()

    assert not doc_exists(opensearch, SimpleModelSearchApp, obj_id)
    assert (
        f'An error occurred syncing a {SimpleModelSearchApp.name} object with id {obj_id}: '
        'SimpleModel matching query does not exist. '
        f'Object {SimpleModelSearchApp.name} may have been deleted before being synced'
        in caplog.text
    )
