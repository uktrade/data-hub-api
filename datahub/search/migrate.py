from logging import getLogger

from datahub.core.exceptions import DataHubException
from datahub.search.elasticsearch import create_index, start_alias_transaction
from datahub.search.tasks import complete_model_migration, sync_model

logger = getLogger(__name__)


def migrate_apps(apps):
    """Migrates all search apps to new indices if their mappings are out of date."""
    logger.info('Starting search app migration')
    for app in apps:
        migrate_app(app)


def migrate_app(search_app):
    """Migrates a search app to a new index (if its mapping is out of date)."""
    app_name = search_app.name
    es_model = search_app.es_model

    is_new_index = es_model.set_up_index_and_aliases()

    if is_new_index:
        _schedule_initial_sync(search_app)
        return

    if es_model.is_migration_needed():
        _perform_migration(search_app)
        return

    if es_model.was_migration_started():
        logger.info(f'Possibly incomplete {app_name} search app migration detected')
        _schedule_resync(search_app)
        return

    logger.info(f'{app_name} search app is up to date')


def _perform_migration(search_app):
    app_name = search_app.name
    es_model = search_app.es_model
    logger.info(f'Migrating the {app_name} search app')

    read_alias_name = es_model.get_read_alias()
    write_alias_name = es_model.get_write_alias()
    new_index_name = es_model.get_target_index_name()

    current_read_indices, current_write_index = es_model.get_read_and_write_indices()

    if current_write_index not in current_read_indices:
        raise DataHubException(
            'Cannot migrate Elasticsearch index with a read alias referencing '
            'a different index to the write alias',
        )

    logger.info(f'Updating aliases for the {app_name} search app')

    create_index(new_index_name, es_model._doc_type.mapping)

    with start_alias_transaction() as alias_transaction:
        alias_transaction.associate_indices_with_alias(read_alias_name, [new_index_name])
        alias_transaction.associate_indices_with_alias(write_alias_name, [new_index_name])
        alias_transaction.dissociate_indices_from_alias(write_alias_name, [current_write_index])

    _schedule_resync(search_app)


def _schedule_resync(search_app):
    logger.info(f'Scheduling resync and clean-up for the {search_app.name} search app')
    complete_model_migration.apply_async(
        args=(search_app.name, search_app.es_model.get_target_mapping_hash()),
    )


def _schedule_initial_sync(search_app):
    logger.info(f'Scheduling initial sync for the {search_app.name} search app')
    sync_model.apply_async(args=(search_app.name,))
