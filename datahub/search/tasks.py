from celery import shared_task
from celery.utils.log import get_task_logger
from django_pglocks import advisory_lock

from datahub.search.apps import get_search_app, get_search_apps
from datahub.search.bulk_sync import sync_app
from datahub.search.migrate_utils import resync_after_migrate


logger = get_task_logger(__name__)


@shared_task(acks_late=True, priority=9)
def sync_all_models():
    """
    Task that starts sub-tasks to sync all models to Elasticsearch.

    acks_late is set to True so that the task restarts if interrupted.

    priority is set to the lowest priority (for Redis, 0 is the highest priority).
    """
    for search_app in get_search_apps():
        sync_model.apply_async(
            args=(search_app.name,),
        )


@shared_task(acks_late=True, priority=9)
def sync_model(search_app_name):
    """
    Task that syncs a single model to Elasticsearch.

    acks_late is set to True so that the task restarts if interrupted.

    priority is set to the lowest priority (for Redis, 0 is the highest priority).
    """
    search_app = get_search_app(search_app_name)
    sync_app(search_app)


@shared_task(bind=True, acks_late=True, priority=7, max_retries=5, default_retry_delay=60)
def migrate_model(self, search_app_name, new_mapping_hash):
    """Completes a migration by performing a full resync."""
    search_app = get_search_app(search_app_name)
    if search_app.es_model.get_target_mapping_hash() != new_mapping_hash:
        logger.info(
            f'Unexpected target mapping hash, an old app instance may have received this task. '
            f'Rescheduling {search_app_name} search app migration...'
        )
        raise self.retry()

    with advisory_lock(f'leeloo-resync_after_migrate-{search_app_name}'):
        resync_after_migrate(search_app)
