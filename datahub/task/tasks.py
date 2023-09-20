import logging

from datahub.core.queues.constants import HALF_DAY_IN_SECONDS
from datahub.core.queues.job_scheduler import job_scheduler
from datahub.core.queues.scheduler import LONG_RUNNING_QUEUE
from datahub.reminder.models import UpcomingTaskReminderSubscription

logger = logging.getLogger(__name__)


def schedule_create_task_reminder_subscription_task(task_id):
    print('******** Hello I scheduled a thing')
    from pprint import pprint

    print('******** scheduled', task_id)
    job = job_scheduler(
        queue_name=LONG_RUNNING_QUEUE,
        function=create_task_reminder_subscription_task,
        function_args=(task_id,),
        job_timeout=HALF_DAY_IN_SECONDS,
        max_retries=5,
        retry_backoff=True,
        retry_intervals=30,
    )
    logger.info(
        f'Task {job.id} create_task_reminder_subscription_task',
    )
    return job


def create_task_reminder_subscription_task(task_id):
    """
    Creates a task reminder subscription doe an adviser if the adviser doesn't have on already.
    """
    from pprint import pprint

    print('******** The task', task_id)
    # try:
    #     instance = UpcomingTaskReminderSubscription.objects.get(adviser=adviser_id)
    # except UpcomingTaskReminderSubscription.DoesNotExist:
    #     print('Create the task reminder subscription')
    #     UpcomingTaskReminderSubscription.objects.create(adviser=adviser_id)
    # else:
    #     print('Do not create the task reminder subscription')
