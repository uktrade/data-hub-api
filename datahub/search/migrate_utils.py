from logging import getLogger

from datahub.core.exceptions import DataHubError
from datahub.search.bulk_sync import sync_app
from datahub.search.deletion import delete_documents
from datahub.search.elasticsearch import (
    delete_index,
    get_aliases_for_index,
    start_alias_transaction,
)


BULK_DELETION_TIMEOUT_SECS = 300
logger = getLogger(__name__)


def resync_after_migrate(search_app):
    """
    Completes a migration by performing a full resync, updating aliases and removing old indices.
    """
    if not search_app.es_model.was_migration_started():
        logger.warning(
            f'No pending migration detected for the {search_app.name} search app, aborting '
            f'resync...',
        )
        return

    sync_app(search_app, post_batch_callback=delete_from_secondary_indices_callback)
    _clean_up_aliases_and_indices(search_app)


def _clean_up_aliases_and_indices(search_app):
    es_model = search_app.es_model
    read_alias = es_model.get_read_alias()
    read_indices, write_index = es_model.get_read_and_write_indices()

    if write_index not in read_indices:
        raise DataHubError('Write index not in read alias, aborting mapping migration...')

    indices_to_remove = read_indices - {write_index}

    if indices_to_remove:
        with start_alias_transaction() as alias_transaction:
            alias_transaction.dissociate_indices_from_alias(read_alias, indices_to_remove)
    else:
        logger.warning(f'No indices to remove for the {read_alias} alias')

    for index in indices_to_remove:
        if not get_aliases_for_index(index):
            delete_index(index)


def delete_from_secondary_indices_callback(read_indices, write_index, actions):
    """
    Callback for sync_app() and sync_objects() that deletes synced documents from any indices
    that are currently being migrated from.

    This is used to avoid multiple, differing copies of documents existing at the same time
    whilst documents are being migrated from one index to another.
    """
    remove_indices = read_indices - {write_index}
    for index in remove_indices:
        delete_documents(index, actions)
