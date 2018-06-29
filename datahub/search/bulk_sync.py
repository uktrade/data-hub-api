from logging import getLogger

from datahub.core.utils import slice_iterable_into_chunks
from datahub.search.elasticsearch import bulk

logger = getLogger(__name__)

PROGRESS_INTERVAL = 20000
BULK_INDEX_TIMEOUT_SECS = 300


def sync_app(search_app, batch_size=None, post_batch_callback=None):
    """Syncs objects for an app to ElasticSearch in batches of batch_size."""
    model_name = search_app.es_model.__name__
    batch_size = batch_size or search_app.bulk_batch_size
    logger.info(f'Processing {model_name} records, using batch size {batch_size}')

    read_indices, write_index = search_app.es_model.get_read_and_write_indices()

    rows_processed = 0
    total_rows = search_app.queryset.count()
    it = search_app.queryset.iterator(chunk_size=batch_size)
    batches = slice_iterable_into_chunks(it, batch_size)
    for batch in batches:
        actions = list(search_app.es_model.db_objects_to_es_documents(batch, index=write_index))
        num_actions = len(actions)
        bulk(
            actions=actions,
            chunk_size=num_actions,
            request_timeout=BULK_INDEX_TIMEOUT_SECS,
        )

        if post_batch_callback:
            post_batch_callback(read_indices, write_index, actions)

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
