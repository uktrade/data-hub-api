from logging import getLogger

from datahub.core.queue import job_scheduler
from datahub.search.bulk_sync import sync_objects
from datahub.search.migrate_utils import delete_from_secondary_indices_callback
from datahub.search.tasks import sync_object_task, sync_related_objects_task

logger = getLogger(__name__)


def sync_object(search_app, pk):
    """
    Syncs a single object to OpenSearch.

    This function is migration-safe – if a migration is in progress, the object is added to the
    new index and then deleted from the old index.
    """
    search_model = search_app.search_model
    read_indices, write_index = search_model.get_read_and_write_indices()

    obj = search_app.queryset.get(pk=pk)
    sync_objects(
        search_model,
        [obj],
        read_indices,
        write_index,
        post_batch_callback=delete_from_secondary_indices_callback,
    )


def sync_object_async(search_app, pk):
    """
    Syncs a single object to OpenSearch asynchronously (by scheduling a Celery task).

    This function is normally used by signal receivers to copy new or updated objects to
    OpenSearch.

    Syncing an object is migration-safe – if a migration is in progress, the object is
    added to the new index and then deleted from the old index.
    """
    job_scheduler(
        function=sync_object_task,
        function_args=(
            search_app.name,
            pk,
        ),
        max_retries=15,
        retry_backoff=True,
    )
    logger.info(
        f'Task sync_object_task {search_app.name} '
        f'scheduled to synchronise object {pk} '
        f'for search app {search_app.name}',
    )


def sync_related_objects_async(related_obj, related_obj_field_name, related_obj_filter=None):
    """
    Syncs objects related to another object via a specified field.

    For example, this function would sync the interactions of a company if given the following
    arguments:
        related_obj=company
        related_obj_field_name='interactions'

    This function is normally used by signal receivers to copy new or updated related objects to
    OpenSearch.
    """
    kwargs = {'related_obj_filter': related_obj_filter} if related_obj_filter else {}
    job_scheduler(
        function=sync_related_objects_task,
        function_args=(
            related_obj._meta.label,
            str(related_obj.pk),
            related_obj_field_name,
        ),
        function_kwargs=kwargs,
        max_retries=15,
        retry_backoff=True,
    )
    logger.info(
        f'Task sync_related_objects_async scheduled to '
        f' synchronise {related_obj_field_name} for object'
        f' {related_obj.pk}',
    )
