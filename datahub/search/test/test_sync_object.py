import pytest

from datahub.search.sync_object import sync_object_async, sync_related_objects_async
from datahub.search.test.search_support.models import RelatedModel, SimpleModel
from datahub.search.test.search_support.relatedmodel import RelatedModelSearchApp
from datahub.search.test.search_support.simplemodel import SimpleModelSearchApp
from datahub.search.test.utils import doc_exists


@pytest.mark.django_db
def test_sync_object_task_syncs_using_celery(setup_es):
    """Test that an object can be synced to Elasticsearch using Celery."""
    obj = SimpleModel.objects.create()
    sync_object_async(SimpleModelSearchApp, obj.pk)
    setup_es.indices.refresh()

    assert doc_exists(setup_es, SimpleModelSearchApp, obj.pk)


@pytest.mark.django_db
def test_sync_related_objects_syncs_using_celery(setup_es):
    """Test that related objects can be synced to Elasticsearch using Celery."""
    simpleton = SimpleModel.objects.create()
    relation_1 = RelatedModel.objects.create(simpleton=simpleton)
    relation_2 = RelatedModel.objects.create(simpleton=simpleton)
    unrelated_obj = RelatedModel.objects.create()

    sync_related_objects_async(simpleton, 'relatedmodel_set')
    setup_es.indices.refresh()

    assert doc_exists(setup_es, RelatedModelSearchApp, relation_1.pk)
    assert doc_exists(setup_es, RelatedModelSearchApp, relation_2.pk)
    assert not doc_exists(setup_es, RelatedModelSearchApp, unrelated_obj.pk)
