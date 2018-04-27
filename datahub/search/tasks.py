from celery import shared_task

from datahub.search.apps import get_search_app, SEARCH_APPS
from datahub.search.bulk_sync import sync_dataset


@shared_task(acks_late=True, priority=9)
def sync_all_models():
    """
    Task that starts sub-tasks to sync all models to Elasticsearch.

    acks_late is set to True so that the task restarts if interrupted.

    priority is set to the lowest priority (for Redis, 0 is the highest priority).
    """
    for search_app_cls_path in SEARCH_APPS:
        sync_model.apply_async(
            args=(search_app_cls_path,),
        )


@shared_task(acks_late=True, priority=9)
def sync_model(search_app_cls_path):
    """
    Task that syncs a single model to Elasticsearch.

    acks_late is set to True so that the task restarts if interrupted.

    priority is set to the lowest priority (for Redis, 0 is the highest priority).
    """
    search_app = get_search_app(search_app_cls_path)
    sync_dataset(search_app.get_dataset())
