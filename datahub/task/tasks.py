import logging

from datahub.core.queues.job_scheduler import job_scheduler
from datahub.core.queues.scheduler import LONG_RUNNING_QUEUE
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
