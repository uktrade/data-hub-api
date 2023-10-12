import logging

from datahub.core.queues.constants import HALF_DAY_IN_SECONDS
from datahub.core.queues.job_scheduler import job_scheduler
from datahub.core.queues.scheduler import LONG_RUNNING_QUEUE
from datahub.reminder.models import UpcomingTaskReminderSubscription
from datahub.task.models import Task

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
    # if not is_user_feature_flag_active(
    #     ADVISER_TASKS_USER_FEATURE_FLAG_NAME,
    #     subscription.adviser,
    # ):
    #     logger.info(
    #         f'Feature flag {ADVISER_TASKS_USER_FEATURE_FLAG_NAME}' ' is not active, exiting.',
    #     )
    #     return

    tasks = Task.objects.filter(reminder_days__gt=0)

    # from pprint import pprint

    # pprint(tasks.__dict__)
    return tasks
    # tasks [due_date - reminder_days = today]
    #   advisers [is_active && ]
    #       upcoming_task_reminder_subscription [select email_reminder_enabled]

    #   userfeatureflag or userfeatureflag group set

    # Add reminder to DataHub reminders
    # Send email if upcoming_task_reminder_subscription.email_reminder_enabled


# Q(due_date-reminder_days=today)
# Select all Reminders that are due for advisers that have active feature flag
# Schedule reminder/notification
# return Task

# def _get_active_projects(adviser):
#     """
#     Get active projects for given adviser.
#     """
#     return InvestmentProject.objects.filter(
#         Q(project_manager=adviser)
#         | Q(project_assurance_adviser=adviser)
#         | Q(client_relationship_manager=adviser)
#         | Q(referral_source_adviser=adviser),
#         status__in=[
#             InvestmentProject.Status.ONGOING,
#             InvestmentProject.Status.DELAYED,
#         ],
#         stage_id=InvestmentProjectStage.active.value.id,
#     )
