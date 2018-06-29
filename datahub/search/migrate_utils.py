from logging import getLogger

from datahub.core.exceptions import DataHubException
from datahub.search.bulk_sync import sync_app
from datahub.search.elasticsearch import (
    bulk,
    delete_index,
    get_aliases_for_index,
    start_alias_transaction,
)


BULK_DELETION_TIMEOUT_SECS = 300
logger = getLogger(__name__)


def resync_after_migrate(search_app):
    """Resyncs all documents in an index following a migration."""
    if not search_app.es_model.was_migration_started():
        logger.warning(
            f'No pending migration detected for the {search_app.name} search app, aborting '
            f'resync...'
        )
        return

    sync_app(search_app, post_batch_callback=_sync_app_post_batch_callback)

    es_model = search_app.es_model
    read_alias = es_model.get_read_alias()
    read_indices, write_index = es_model.get_read_and_write_indices()

    if write_index not in read_indices:
        raise DataHubException('Write index not in read alias, aborting mapping migration...')

    indices_to_remove = read_indices - {write_index}

    if indices_to_remove:
        with start_alias_transaction() as alias_transaction:
            alias_transaction.dissociate_indices_from_alias(read_alias, indices_to_remove)
    else:
        logger.warning(f'No indices to remove for the {read_alias} alias')

    for index in indices_to_remove:
        _delete_old_index(index)


def _delete_old_index(index):
    if not get_aliases_for_index(index):
        delete_index(index)


def _sync_app_post_batch_callback(read_indices, write_index, actions):
    remove_indices = read_indices - {write_index}
    for index in remove_indices:
        _delete_documents(index, actions)


def _delete_documents(index, es_docs):
    delete_actions = [
        _create_delete_action(index, action['_type'], action['_id'])
        for action in es_docs
    ]

    _, errors = bulk(
        actions=delete_actions,
        chunk_size=len(es_docs),
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
