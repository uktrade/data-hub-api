from logging import getLogger

from datahub.core.exceptions import DataHubError
from datahub.core.queues.job_scheduler import job_scheduler
from datahub.core.queues.scheduler import LONG_RUNNING_QUEUE
from datahub.search.opensearch import create_index, start_alias_transaction
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
    search_model = search_app.search_model

    is_new_index = search_model.set_up_index_and_aliases()

    if is_new_index:
        _schedule_initial_sync(search_app)
        return

    if search_model.is_migration_needed():
        _perform_migration(search_app)
        return

    if search_model.was_migration_started():
        logger.info(f'Possibly incomplete {app_name} search app migration detected')
        _schedule_resync(search_app)
        return

    logger.info(f'{app_name} search app is up to date')


def _perform_migration(search_app):
    app_name = search_app.name
    search_model = search_app.search_model
    logger.info(f'Migrating the {app_name} search app')

    read_alias_name = search_model.get_read_alias()
    write_alias_name = search_model.get_write_alias()
    new_index_name = search_model.get_target_index_name()

    current_read_indices, current_write_index = search_model.get_read_and_write_indices()

    if current_write_index not in current_read_indices:
        raise DataHubError(
            'Cannot migrate OpenSearch index with a read alias referencing '
            'a different index to the write alias',
        )

    logger.info(f'Updating aliases for the {app_name} search app')

    create_index(new_index_name, search_model._doc_type.mapping)

    with start_alias_transaction() as alias_transaction:
        alias_transaction.associate_indices_with_alias(read_alias_name, [new_index_name])
        alias_transaction.associate_indices_with_alias(write_alias_name, [new_index_name])
        alias_transaction.dissociate_indices_from_alias(write_alias_name, [current_write_index])

    _schedule_resync(search_app)


def _schedule_resync(search_app):
    logger.info(f'Scheduling resync and clean-up for the {search_app.name} search app')
    job = job_scheduler(
        queue_name=LONG_RUNNING_QUEUE,
        function=complete_model_migration,
        function_args=(search_app.name, search_app.search_model.get_target_mapping_hash()),
        max_retries=5,
        retry_intervals=60,
        job_timeout=1800,
    )
    logger.info(
        f'Task {job.id} complete model migration is scheduled for {search_app.name}',
    )


def _schedule_initial_sync(search_app):
    logger.info(f'Scheduling initial sync for the {search_app.name} search app')
    job = job_scheduler(
        queue_name=LONG_RUNNING_QUEUE,
        function=sync_model,
        function_args=(search_app.name,),
        job_timeout=600,
    )
    logger.info(f'Scheduling with {job.id} for initial sync for the {search_app.name} search app')
