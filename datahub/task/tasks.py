import logging

from datahub.core.queues.constants import HALF_DAY_IN_SECONDS
from datahub.core.queues.job_scheduler import job_scheduler
from datahub.core.queues.scheduler import LONG_RUNNING_QUEUE
from datahub.feature_flag.utils import is_user_feature_flag_active
from datahub.reminder import ADVISER_TASKS_USER_FEATURE_FLAG_NAME
from datahub.reminder.models import UpcomingTaskReminderSubscription

logger = logging.getLogger(__name__)


def schedule_create_task_reminder_subscription_task(advisers):
    for adviser in advisers:
        job = job_scheduler(
            queue_name=LONG_RUNNING_QUEUE,
            function=create_task_reminder_subscription_task,
            function_args=(adviser,),
        )
        logger.info(
            f'Task {job.id} create_task_reminder_subscription_task',
        )


def create_task_reminder_subscription_task(adviser):
    """
    Creates a task reminder subscription for an adviser if the adviser doesn't have
    a subscription already.
    """
    try:
        UpcomingTaskReminderSubscription.objects.get(adviser=adviser)
    except UpcomingTaskReminderSubscription.DoesNotExist:
        UpcomingTaskReminderSubscription.objects.create(adviser=adviser)


def schedule_reminders_upcoming_tasks():
    job = job_scheduler(
        queue_name=LONG_RUNNING_QUEUE,
        function=generate_reminders_upcoming_tasks,
        job_timeout=HALF_DAY_IN_SECONDS,
        max_retries=5,
        retry_backoff=True,
        retry_intervals=30,
    )
    logger.info(
        f'Task {job.id} generate_reminders_upcoming_tasks scheduled',
    )
    return job


def generate_reminders_upcoming_tasks():
    if not is_user_feature_flag_active(
        ADVISER_TASKS_USER_FEATURE_FLAG_NAME,
    ):
        logger.info(
            f'Feature flag {ADVISER_TASKS_USER_FEATURE_FLAG_NAME}' ' is not active, exiting.',
        )
        return

    # return Task
