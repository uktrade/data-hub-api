from celery import shared_task

from datahub.search.apps import get_search_app, get_search_apps
from datahub.search.bulk_sync import sync_app


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
