import logging

from django.conf import settings
from django.utils import timezone
from django_pglocks import advisory_lock

from datahub.core import statsd
from datahub.core.queues.constants import HALF_DAY_IN_SECONDS
from datahub.core.queues.job_scheduler import job_scheduler
from datahub.core.queues.scheduler import LONG_RUNNING_QUEUE
from datahub.feature_flag.utils import is_user_feature_flag_active
from datahub.reminder import ADVISER_TASKS_USER_FEATURE_FLAG_NAME
from datahub.reminder.models import (
    TaskAssignedToMeFromOthersSubscription,
    UpcomingTaskReminder,
    UpcomingTaskReminderSubscription,
)
from datahub.reminder.tasks import notify_adviser_by_rq_email
from datahub.task.models import Task

from datahub.task.client import Notify

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
        UpcomingTaskReminderSubscription.objects.create(
            adviser=adviser,
            email_reminders_enabled=True,
        )


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
    with advisory_lock(
        'generate_reminders_upcoming_tasks',
        wait=False,
    ) as acquired:
        if not acquired:
            logger.info(
                'Reminders for upcoming tasks are already being processed by another worker.',
            )
            return
        now = timezone.now()
        # When adding additional tasks this query will need to be moved to Open Search to return
        # all task types.
        tasks = Task.objects.filter(reminder_date=now)
        for task in tasks:
            # Get all active advisers assigned to the task
            active_advisers = task.advisers.filter(is_active=True)
            for adviser in active_advisers:
                # Get subscription to know if emails are needed
                adviser_subscription = UpcomingTaskReminderSubscription.objects.filter(
                    adviser=adviser,
                ).first()
                if adviser_subscription:
                    create_upcoming_task_reminder(
                        task,
                        adviser,
                        adviser_subscription.email_reminders_enabled,
                        now,
                    )

        logger.info(
            'Task generate_reminders_upcoming_tasks completed',
        )
        return tasks


def create_upcoming_task_reminder(
    task,
    adviser,
    send_email,
    current_date,
):
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
    )

    if send_email and is_user_feature_flag_active(
        ADVISER_TASKS_USER_FEATURE_FLAG_NAME,
        adviser,
    ):
        send_task_reminder_email(
            adviser=adviser,
            task=task,
            company=task.get_company(),
            reminders=[reminder],
        )

    return reminder


def _has_existing_upcoming_task_reminder(task, adviser, current_date):
    return UpcomingTaskReminder.objects.filter(
        task=task,
        adviser=adviser,
        created_on__month=current_date.month,
        created_on__year=current_date.year,
    ).exists()


def send_task_reminder_email(
    adviser,
    task,
    company,
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
            'company_name': company.name,
            'task_due_date': task.due_date.strftime('%-d %B %Y'),
            'task_url': task.get_absolute_url(),
        },
        update_task=update_task_reminder_email_status,
        reminders=reminders,
    )


def update_task_reminder_email_status(email_notification_id, reminder_ids):
    reminders = UpcomingTaskReminder.all_objects.filter(id__in=reminder_ids)
    for reminder in reminders:
        reminder.email_notification_id = email_notification_id
        reminder.save()


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


def send_notification_task_assigned_from_others_email_task(self, task, adviser):
    """
    Sends an email when an adviser is added to a task.
    """
    Notify.notify_adviser_added_to_task(self, task, adviser)
