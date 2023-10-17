import logging

from django.conf import settings
from django.utils import timezone

from datahub.core import statsd
from datahub.core.queues.constants import HALF_DAY_IN_SECONDS
from datahub.core.queues.job_scheduler import job_scheduler
from datahub.core.queues.scheduler import LONG_RUNNING_QUEUE
from datahub.reminder.models import (
    UpcomingTaskReminder,
    UpcomingTaskReminderSubscription,
)
from datahub.reminder.tasks import notify_adviser_by_rq_email
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
        # print("task: ", task)
        # print("active_advisers: ", active_advisers)
        for adviser in active_advisers:
            # userfeatureflag or userfeatureflag group set

            # print("adviser:", adviser)
            # Schedule bell reminder

            # GET SUBSCRIPTION TO KNOW IF EMAILS ARE NEEDED
            adviser_subscription = UpcomingTaskReminderSubscription.objects.filter(adviser=adviser)

            create_upcoming_task_reminder(task, adviser, adviser_subscription, now)

            # If subscription send email

    #         print("adviser_subscription:", adviser_subscription)

    # print("tasks:", tasks)

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


def create_upcoming_task_reminder(task, adviser, send_email, current_date):
    """
    Creates a reminder and sends an email if required.

    If a reminder has already been sent on the same day, then do nothing.
    """
    if _has_existing_upcoming_task_reminder(task, adviser, current_date):
        return

    reminder = UpcomingTaskReminder.objects.create(
        adviser=adviser,
        event=f'{task.reminder_days} days left to task due',
        task=task,
        # project=task,
    )

    # from pprint import pprint
    # pprint("reminder: ", reminder.__dict__)

    if send_email:
        # print('send_email: sending...')
        send_task_reminder_email(
            adviser=adviser,
            task=task,
            reminders=[reminder],
        )

    return reminder


def _has_existing_upcoming_task_reminder(investment_project_task, adviser, current_date):
    return UpcomingTaskReminder.objects.filter(
        adviser=adviser,
        # investment_project_task=investment_project_task,
        created_on__month=current_date.month,
        created_on__year=current_date.year,
    ).exists()


def send_task_reminder_email(
    adviser,
    task,
    reminders,
):
    """
    Sends task reminder by email.
    """
    statsd.incr(f'send_task_reminder_notification.{task.reminder_days}')

    notify_adviser_by_rq_email(
        adviser=adviser,
        template_identifier=settings.TASK_REMINDER_STATUS_TEMPLATE_ID,
        context={
            'task_title': task.title,
            'company_name': '',
            'task_due_date': task.due_date,
            'company_contact_email_address': '',
            'task_url': '',
            'complete_task_url': '',
        },
        update_task=update_task_reminder_email_status,
        reminders=reminders,
    )


def update_task_reminder_email_status(email_notification_id, reminder_ids):
    reminders = UpcomingTaskReminder.all_objects.filter(id__in=reminder_ids)
    for reminder in reminders:
        reminder.email_notification_id = email_notification_id
        reminder.save()


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
