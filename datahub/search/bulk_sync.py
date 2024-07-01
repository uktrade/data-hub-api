from logging import getLogger

from django.core.exceptions import FieldError

from datahub.core.utils import slice_iterable_into_chunks
from datahub.search.opensearch import bulk

logger = getLogger(__name__)

PROGRESS_INTERVAL = 20000
BULK_INDEX_TIMEOUT_SECS = 300


def sync_app(search_app, batch_size=None, post_batch_callback=None):
    """Syncs objects for an app to OpenSearch in batches of batch_size."""
    model_name = search_app.search_model.__name__
    batch_size = batch_size or search_app.bulk_batch_size
    logger.info(f'Processing {model_name} records, using batch size {batch_size}')

    read_indices, write_index = search_app.search_model.get_read_and_write_indices()

    num_source_rows_processed = 0
    num_objects_synced = 0
    total_rows = search_app.queryset.count()

    # We know pk exists but some models don't have modified_on, so handle this.
    try:
        it = search_app.queryset.order_by('-modified_on').values_list('pk', flat=True).iterator(chunk_size=batch_size)
        has_modified_on = True
    except FieldError:
        it = search_app.queryset.values_list('pk', flat=True).iterator(chunk_size=batch_size)
        has_modified_on = False

    batches = slice_iterable_into_chunks(it, batch_size)
    for batch in batches:
        objs = search_app.queryset.filter(pk__in=batch)

        num_actions = sync_objects(
            search_app.search_model,
            objs,
            read_indices,
            write_index,
            post_batch_callback=post_batch_callback,
        )

        emit_progress = (
            (num_source_rows_processed + num_actions) // PROGRESS_INTERVAL
            - num_source_rows_processed // PROGRESS_INTERVAL
            > 0
        )

        num_source_rows_processed += len(batch)
        num_objects_synced += num_actions

        if emit_progress:
            log_message = (
                f'{model_name} rows processed: {num_source_rows_processed}/{total_rows} '
                f'{num_source_rows_processed*100//total_rows}%'
            )

            if has_modified_on:
                log_message = f'{log_message} modified_on: {objs.last().modified_on}'

            logger.info(log_message)

    logger.info(f'{model_name} rows processed: {num_source_rows_processed}/{total_rows} 100%.')
    if num_source_rows_processed != num_objects_synced:
        logger.warning(
            f'{num_source_rows_processed - num_objects_synced} deleted objects detected while '
            f'syncing model {model_name}',
        )


def sync_objects(search_model, model_objects, read_indices, write_index, post_batch_callback=None):
    """Syncs an iterable of model instances to OpenSearch."""
    actions = list(
        search_model.db_objects_to_documents(model_objects, index=write_index),
    )
    num_actions = len(actions)
    bulk(
        actions=actions,
        chunk_size=num_actions,
        request_timeout=BULK_INDEX_TIMEOUT_SECS,
    )

    if post_batch_callback:
        post_batch_callback(read_indices, write_index, actions)

    return num_actions
