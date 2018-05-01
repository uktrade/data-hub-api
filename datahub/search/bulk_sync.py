from logging import getLogger

from datahub.core.utils import slice_iterable_into_chunks
from datahub.search.apps import get_search_apps
from datahub.search.elasticsearch import bulk

logger = getLogger(__name__)

DEFAULT_BATCH_SIZE = 1000
PROGRESS_INTERVAL = 20000


def get_datasets(models=None):
    """
    Returns datasets that will be synchronised with Elasticsearch.

    :param models: list of search app names to index, None for all
    """
    search_apps = get_search_apps()

    # if models empty, assume all models
    if not models:
        models = [search_app.name for search_app in search_apps]

    return [
        search_app.get_dataset()
        for search_app in search_apps
        if search_app.name in models
    ]


def sync_dataset(item, batch_size=DEFAULT_BATCH_SIZE):
    """Sends dataset to ElasticSearch in batches of batch_size."""
    model_name = item.es_model.__name__
    logger.info(f'Processing {model_name} records...')

    rows_processed = 0
    total_rows = item.queryset.count()
    it = item.queryset.iterator(chunk_size=batch_size)
    batches = slice_iterable_into_chunks(it, batch_size)
    for batch in batches:
        actions = list(item.es_model.dbmodels_to_es_documents(batch))
        num_actions = len(actions)
        bulk(
            actions=actions,
            chunk_size=num_actions,
            request_timeout=300,
            raise_on_error=True,
            raise_on_exception=True,
        )

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
