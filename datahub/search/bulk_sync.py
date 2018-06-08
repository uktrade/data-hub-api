from logging import getLogger

from datahub.core.exceptions import DataHubException
from datahub.core.utils import slice_iterable_into_chunks
from datahub.search.apps import get_search_apps
from datahub.search.elasticsearch import bulk

logger = getLogger(__name__)

PROGRESS_INTERVAL = 20000
BULK_INDEX_TIMEOUT_SECS = 300
BULK_DELETION_TIMEOUT_SECS = 300


def get_apps_to_sync(models=None):
    """
    Returns apps that will be synchronised with Elasticsearch.

    :param models: list of search app names to index, None for all
    """
    search_apps = get_search_apps()

    # if models empty, assume all models
    return [search_app for search_app in search_apps if not models or search_app.name in models]


def sync_app(item, batch_size=None):
    """Syncs objects for an app to ElasticSearch in batches of batch_size."""
    model_name = item.es_model.__name__
    batch_size = batch_size or item.bulk_batch_size
    logger.info(f'Processing {model_name} records, using batch size {batch_size}')

    read_indices, write_index = item.es_model.get_read_and_write_indices()
    remove_indices = read_indices - {write_index}

    rows_processed = 0
    total_rows = item.queryset.count()
    it = item.queryset.iterator(chunk_size=batch_size)
    batches = slice_iterable_into_chunks(it, batch_size)
    for batch in batches:
        actions = list(item.es_model.db_objects_to_es_documents(batch, index=write_index))
        num_actions = len(actions)
        bulk(
            actions=actions,
            chunk_size=num_actions,
            request_timeout=BULK_INDEX_TIMEOUT_SECS,
        )

        for index in remove_indices:
            _delete_documents(index, actions)

        emit_progress = (
            (rows_processed + num_actions) // PROGRESS_INTERVAL
            - rows_processed // PROGRESS_INTERVAL
            > 0
        )

        rows_processed += num_actions

        if emit_progress:
            logger.info(f'{model_name} rows processed: {rows_processed}/{total_rows} '
                        f'{rows_processed*100//total_rows}%')

    logger.info(f'{model_name} rows processed: {rows_processed}/{total_rows} 100%.')


def _delete_documents(index, complete_index_actions):
    delete_actions = (
        _create_delete_action(index, action['_type'], action['_id'])
        for action in complete_index_actions
    )

    _, errors = bulk(
        actions=delete_actions,
        chunk_size=len(complete_index_actions),
        request_timeout=BULK_DELETION_TIMEOUT_SECS,
        raise_on_error=False,
    )

    non_404_errors = [error for error in errors if error['delete']['status'] != 404]
    if non_404_errors:
        raise DataHubException(
            f'One or more errors during an Elasticsearch bulk deletion operation: '
            f'{non_404_errors!r}'
        )


def _create_delete_action(_index, _type, _id):
    return {
        '_op_type': 'delete',
        '_index': _index,
        '_type': _type,
        '_id': _id,
    }
