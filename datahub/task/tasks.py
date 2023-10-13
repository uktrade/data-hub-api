import logging

from django.db.models import (
    DateTimeField,
    DecimalField,
    ExpressionWrapper,
    F,
    IntegerField,
)
from django.db.models.functions import Cast
from django.utils import timezone

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
    now = timezone.now()

    #     set4 = Race.objects.annotate(
    #     diff=ExpressionWrapper(F('end') - F('start'), output_field=DurationField())).filter(
    #     diff__gte=datetime.timedelta(5))
    # len(set4)
    # # 364
    # len(Race.objects.filter(end__gte=F("start")+5))

    tasks = Task.objects.filter(reminder_date=now)
    for task in tasks:
        # GET ALL ACTIVE ADVISERS ASSIGNED TO THE TASK
        active_advisers = task.advisers.filter(is_active=True)
        print(active_advisers)
        for adviser in active_advisers:
            print(adviser)
            # GET SUBSCRIPTION TO KNOW IF EMAILS ARE NEEDED
            adviser_subscription = UpcomingTaskReminderSubscription.objects.filter(adviser=adviser)
            print(adviser_subscription)

    print(tasks)

    # tasks = Task.objects.annotate(
    #     due_date_days=Cast(
    #         ExpressionWrapper(
    #             Cast('due_date', output_field=DateTimeField()) - Cast(now, DateTimeField()),
    #             output_field=IntegerField(),
    #         )
    #         / 86400000000,
    #         output_field=DecimalField(),
    #     ),
    # ).filter(due_date_days=F('reminder_days'))
    # Cast(
    #     Cast('due_date', output_field=DateTimeField()) - Cast(now, DateTimeField()),
    #     output_field=DurationField(),
    # )

    # tasks = Task.objects.filter(
    #     Q(
    #         reminder_days=
    #     )
    # )

    # from pprint import pprint

    # pprint(tasks.get().__dict__)
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
