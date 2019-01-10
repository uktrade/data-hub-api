from logging import getLogger

from datahub.search.bulk_sync import sync_objects
from datahub.search.migrate_utils import delete_from_secondary_indices_callback
from datahub.search.tasks import sync_object_task, sync_related_objects_task

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
    result = sync_object_task.apply_async(args=(search_app.name, pk))
    logger.info(
        f'Task {result.id} scheduled to synchronise object {pk} for search app '
        f'{search_app.name}',
    )


def sync_related_objects_async(related_obj, related_obj_field_name):
    """
    Syncs objects related to another object via a specified field.

    For example, this function would sync the interactions of a company if given the following
    arguments:
        related_obj=company
        related_obj_field_name='interactions'

    This function is normally used by signal receivers to copy new or updated related objects to
    Elasticsearch.
    """
    result = sync_related_objects_task.apply_async(
        args=(
            related_obj._meta.label,
            str(related_obj.pk),
            related_obj_field_name,
        ),
    )
    logger.info(
        f'Task {result.id} scheduled to synchronise {related_obj_field_name} for object'
        f' {related_obj.pk}',
    )
