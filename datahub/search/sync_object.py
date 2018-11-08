from logging import getLogger

from django.conf import settings

from datahub.core.thread_pool import submit_to_thread_pool
from datahub.search.bulk_sync import sync_objects
from datahub.search.migrate_utils import delete_from_secondary_indices_callback
from datahub.search.tasks import sync_object_task


logger = getLogger(__name__)


def sync_object(search_app, pk):
    """
    Syncs a single object to Elasticsearch.

    This function is migration-safe – if a migration is in progress, the object is added to the
    new index and then deleted from the old index.
    """
    es_model = search_app.es_model
    read_indices, write_index = es_model.get_read_and_write_indices()

    obj = search_app.queryset.get(pk=pk)
    sync_objects(
        es_model,
        [obj],
        read_indices,
        write_index,
        post_batch_callback=delete_from_secondary_indices_callback,
    )


def sync_object_async(search_app, pk):
    """
    Syncs a single object to Elasticsearch asynchronously (by scheduling a Celery task).

    This function is normally used by signal receivers to copy new or updated objects to
    Elasticsearch.

    Syncing an object is migration-safe – if a migration is in progress, the object is
    added to the new index and then deleted from the old index.
    """
    if settings.ENABLE_CELERY_ES_SYNC_OBJECT:
        result = sync_object_task.apply_async(args=(search_app.name, str(pk)))
        logger.info(
            f'Task {result.id} scheduled to synchronise object {pk} for search app '
            f'{search_app.name}',
        )
    else:
        submit_to_thread_pool(sync_object, search_app, pk)
