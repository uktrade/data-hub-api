from logging import getLogger

from django.apps import apps
from django_pglocks import advisory_lock

from datahub.core.queues.constants import HALF_DAY_IN_SECONDS
from datahub.core.queues.errors import RetryError
from datahub.core.queues.job_scheduler import job_scheduler
from datahub.core.queues.scheduler import LONG_RUNNING_QUEUE
from datahub.search.apps import get_search_app, get_search_app_by_model, get_search_apps
from datahub.search.bulk_sync import sync_app
from datahub.search.migrate_utils import resync_after_migrate

logger = getLogger(__name__)


def sync_all_models():
    """Task that starts sub-tasks to sync all models to OpenSearch."""
    for search_app in get_search_apps():
        schedule_model_sync((search_app.name,))


def schedule_model_sync(search_app: tuple):
    job = job_scheduler(
        queue_name=LONG_RUNNING_QUEUE,
        function=sync_model,
        function_args=search_app,
        job_timeout=HALF_DAY_IN_SECONDS,
    )
    logger.info(
        f'Task {job.id} sync_model scheduled for {search_app[0]}',
    )


def sync_model(search_app_name):
    """Task that syncs a single model to OpenSearch."""
    search_app = get_search_app(search_app_name)
    sync_app(search_app)


def sync_object_task(search_app_name, pk):
    """Syncs a single object to OpenSearch.

    If an error occurs, the task will be automatically retried with an exponential back-off.
    The wait between attempts is approximately 2 ** attempt_num seconds (with some jitter
    added).

    This task is named sync_object_task to avoid a conflict with sync_object.
    """
    from datahub.search.sync_object import sync_object

    logger.info(f"Running sync_object_task search_app_name '{search_app_name}' pk '{str(pk)}'")
    search_app = get_search_app(search_app_name)
    sync_object(search_app, pk)


def sync_related_objects_task(
    related_model_label,
    related_obj_pk,
    related_obj_field_name,
    related_obj_filter=None,
    search_app_name=None,
):
    """Syncs objects related to another object via a specified field.

    For example, this task would sync the interactions of a company if given the following
    arguments:
        related_model_label='company.Company'
        related_obj_pk=company.pk
        related_obj_field_name='interactions'

    Note that a lower priority (higher number) is used for syncing related objects, as syncing
    them is less important than syncing the primary object that was modified.

    If an error occurs, the task will be automatically retried with an exponential back-off.
    The wait between attempts is approximately 2 ** attempt_num seconds (with some jitter
    added).

    :param search_app_name: str - Syncs to the given search app if given, used when there are
        multiple search apps for the same DB model as get_search_apps returns the first search app
        associated with a DB model.
    """
    logger.info(
        f"Running sync_related_objects_task '{related_model_label}' "
        f"'{related_obj_pk}' '{related_obj_field_name}' '{related_obj_filter}",
    )
    related_model = apps.get_model(related_model_label)
    related_obj = related_model.objects.get(pk=related_obj_pk)
    manager = getattr(related_obj, related_obj_field_name)
    if related_obj_filter:
        manager = manager.filter(**related_obj_filter)
    queryset = manager.values_list('pk', flat=True)

    # If there are multiple search apps for the same DB model, search_app_name allows
    # you to specify the search app you want to update.
    if search_app_name:
        search_app = get_search_app(search_app_name)
    else:
        search_app = get_search_app_by_model(manager.model)

    for pk in queryset:
        job_scheduler(
            function=sync_object_task,
            function_args=(
                search_app.name,
                pk,
            ),
            max_retries=15,
        )


def complete_model_migration(search_app_name, new_mapping_hash):
    """Completes a migration by performing a full resync, updating aliases and removing old indices."""
    search_app = get_search_app(search_app_name)
    if search_app.search_model.get_target_mapping_hash() != new_mapping_hash:
        warning_message = f"""Unexpected target mapping hash. This indicates that the task was \
generated by either a newer or an older version of the app. This could happen during a blue-green \
deployment where a new app instance creates the task and it's picked up by an old RQ instance.

Rescheduling the {search_app_name} search app migration to attempt to resolve the conflict...
"""
        logger.warning(warning_message)
        raise RetryError(warning_message)

    with advisory_lock(f'leeloo-resync_after_migrate-{search_app_name}', wait=False) as lock_held:
        if not lock_held:
            logger.warning(
                f'Another complete_model_migration task is in progress for the {search_app_name} '
                f'search app. Aborting...',
            )
            return

        resync_after_migrate(search_app)
