from logging import getLogger

from datahub.core.exceptions import DataHubException
from datahub.search.bulk_sync import sync_app
from datahub.search.elasticsearch import (
    delete_index,
    get_aliases_for_index,
    start_alias_transaction,
)


logger = getLogger(__name__)


def resync_after_migrate(search_app):
    """Resyncs all documents in an index following a migration."""
    sync_app(search_app)

    es_model = search_app.es_model
    read_alias = es_model.get_read_alias()
    read_indices, write_index = es_model.get_read_and_write_indices()

    if write_index not in read_indices:
        raise DataHubException('Write index not in read alias, aborting mapping migration...')

    indices_to_remove = read_indices - {write_index}

    if indices_to_remove:
        with start_alias_transaction() as alias_transaction:
            alias_transaction.remove_indices_from_alias(read_alias, indices_to_remove)
    else:
        logger.warning(f'No indices to remove for the {read_alias} alias')

    for index in indices_to_remove:
        _delete_old_index(index)


def _delete_old_index(index):
    if not get_aliases_for_index(index):
        delete_index(index)
