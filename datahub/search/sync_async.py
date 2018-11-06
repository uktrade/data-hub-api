from datahub.search.bulk_sync import sync_objects
from datahub.search.migrate_utils import delete_from_secondary_indices_callback


def _sync_object(search_app, pk):
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
    Syncs a single object to Elasticsearch asynchronously (using the thread pool).

    This function is normally used by signal receivers to copy new or updated objects to
    Elasticsearch.

    This function is migration-safe – if a migration is in progress, the object is added to the
    new index and then deleted from the old index.
    """
    return _sync_object(search_app, pk)
