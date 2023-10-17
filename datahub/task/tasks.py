import logging

from datahub.core.queues.job_scheduler import job_scheduler
from datahub.core.queues.scheduler import LONG_RUNNING_QUEUE
from datahub.reminder.models import (
    TaskAssignedToMeFromOthersSubscription,
    UpcomingTaskReminderSubscription,
)

logger = logging.getLogger(__name__)


def schedule_create_task_reminder_subscription_task(adviser):
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
    if not UpcomingTaskReminderSubscription.objects.filter(adviser=adviser).first():
        UpcomingTaskReminderSubscription.objects.create(adviser=adviser)


def schedule_create_task_assigned_to_me_from_others_subscription_task(adviser):
    job = job_scheduler(
        queue_name=LONG_RUNNING_QUEUE,
        function=create_task_assigned_to_me_from_others_task,
        function_args=(adviser,),
    )
    logger.info(
        f'Task {job.id} create_task_assigned_to_me_from_others_task',
    )


def create_task_assigned_to_me_from_others_task(adviser):
    """
    Creates a task reminder subscription for an adviser if the adviser doesn't have
    a subscription already.
    """
    if not TaskAssignedToMeFromOthersSubscription.objects.filter(adviser=adviser).first():
        TaskAssignedToMeFromOthersSubscription.objects.create(adviser=adviser)
