import logging

from django.conf import settings
from django.utils import timezone
from django_pglocks import advisory_lock

from datahub.company.models import Advisor
from datahub.core.queues.constants import HALF_DAY_IN_SECONDS
from datahub.core.queues.job_scheduler import job_scheduler
from datahub.core.queues.scheduler import LONG_RUNNING_QUEUE
from datahub.feature_flag.utils import is_user_feature_flag_active
from datahub.reminder import ADVISER_TASKS_USER_FEATURE_FLAG_NAME
from datahub.reminder.models import (
    TaskAssignedToMeFromOthersReminder,
    TaskAssignedToMeFromOthersSubscription,
    TaskCompletedReminder,
    TaskCompletedSubscription,
    TaskOverdueSubscription,
    UpcomingTaskReminder,
    UpcomingTaskReminderSubscription,
)
from datahub.reminder.tasks import notify_adviser_by_rq_email
from datahub.task.emails import (
    TaskAssignedToOthersEmailTemplate,
    TaskCompletedEmailTemplate,
    UpcomingTaskEmailTemplate,
)
from datahub.task.models import Task


logger = logging.getLogger(__name__)


def schedule_create_task_reminder_subscription_task(adviser_id):
    job = job_scheduler(
        queue_name=LONG_RUNNING_QUEUE,
        function=create_task_reminder_subscription_task,
        function_args=(adviser_id,),
    )
    logger.info(
        f'Task {job.id} create_task_reminder_subscription_task',
    )


def create_task_reminder_subscription_task(adviser_id):
    """
    Creates a task reminder subscription for an adviser if the adviser doesn't have
    a subscription already.
    """
    if not UpcomingTaskReminderSubscription.objects.filter(adviser_id=adviser_id).first():
        UpcomingTaskReminderSubscription.objects.create(
            adviser_id=adviser_id,
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
        send_task_email(
            adviser=adviser,
            task=task,
            reminders=[reminder],
            update_task=update_task_reminder_email_status,
            email_template_class=UpcomingTaskEmailTemplate,
        )

    return reminder


def _has_existing_upcoming_task_reminder(task, adviser, current_date):
    return UpcomingTaskReminder.objects.filter(
        task=task,
        adviser=adviser,
        created_on__month=current_date.month,
        created_on__year=current_date.year,
    ).exists()


def update_task_reminder_email_status(email_notification_id, reminder_ids):
    reminders = UpcomingTaskReminder.all_objects.filter(id__in=reminder_ids)
    for reminder in reminders:
        reminder.email_notification_id = email_notification_id
        reminder.save()


def update_task_assigned_to_me_from_others_email_status(email_notification_id, reminder_ids):
    reminders = TaskAssignedToMeFromOthersReminder.all_objects.filter(id__in=reminder_ids)
    for reminder in reminders:
        reminder.email_notification_id = email_notification_id
        reminder.save()


def schedule_create_task_assigned_to_me_from_others_subscription_task(task, adviser_id):
    job = job_scheduler(
        queue_name=LONG_RUNNING_QUEUE,
        function=notify_adviser_added_to_task,
        function_args=(task, adviser_id),
    )
    logger.info(
        f'Task {job.id} create_task_assigned_to_me_from_others_task',
    )


def create_task_assigned_to_me_from_others_subscription(adviser):
    """
    Creates a task reminder subscription for an adviser if the adviser doesn't have
    a subscription already.
    """
    current_subscription = TaskAssignedToMeFromOthersSubscription.objects.filter(
        adviser_id=adviser.id,
    ).first()
    if not current_subscription:
        return TaskAssignedToMeFromOthersSubscription.objects.create(
            adviser=adviser,
            email_reminders_enabled=True,
        )
    return current_subscription


def notify_adviser_added_to_task(task, adviser_id):
    """
    Send a notification to the adviser added to the task
    """
    adviser = Advisor.objects.filter(id=str(adviser_id)).first()
    if not adviser:
        return
    reminder = TaskAssignedToMeFromOthersReminder.objects.create(
        adviser=adviser,
        event=f'{task} assigned to me by {task.modified_by.name}',
        task=task,
    )
    task_subscription = create_task_assigned_to_me_from_others_subscription(adviser)

    if task_subscription.email_reminders_enabled is True and is_user_feature_flag_active(
        ADVISER_TASKS_USER_FEATURE_FLAG_NAME,
        adviser,
    ):
        send_task_email(
            adviser=adviser,
            task=task,
            reminders=[reminder],
            update_task=update_task_assigned_to_me_from_others_email_status,
            email_template_class=TaskAssignedToOthersEmailTemplate,
        )


def schedule_create_task_overdue_subscription_task(adviser_id):
    job = job_scheduler(
        queue_name=LONG_RUNNING_QUEUE,
        function=create_task_overdue_subscription_task,
        function_args=(adviser_id,),
    )
    logger.info(
        f'Task {job.id} create_task_overdue_subscription_task',
    )


def create_task_overdue_subscription_task(adviser_id):
    """
    Creates a task overdue subscription for an adviser if the adviser doesn't have
    a subscription already.
    """
    if not TaskOverdueSubscription.objects.filter(adviser_id=adviser_id).first():
        TaskOverdueSubscription.objects.create(
            adviser_id=adviser_id,
            email_reminders_enabled=True,
        )


def update_task_completed_email_status(email_notification_id, reminder_ids):
    reminders = TaskCompletedReminder.all_objects.filter(id__in=reminder_ids)
    for reminder in reminders:
        reminder.email_notification_id = email_notification_id
        reminder.save()


def schedule_create_task_completed_subscription_task(adviser_id):
    job = job_scheduler(
        queue_name=LONG_RUNNING_QUEUE,
        function=create_task_completed_subscription,
        function_args=(adviser_id,),
    )
    logger.info(
        f'Task {job.id} create_task_completed_subscription_task',
    )


def create_task_completed_subscription(adviser_id):
    """
    Creates a task reminder subscription for an adviser if the adviser doesn't have
    a subscription already.
    """
    if not TaskCompletedSubscription.objects.filter(
        adviser_id=adviser_id,
    ).first():
        TaskCompletedSubscription.objects.create(
            adviser_id=adviser_id,
            email_reminders_enabled=True,
        )


def notify_adviser_completed_task(task, created):
    """
    Send a notification to all advisers, excluding the adviser who marked the task as completed,
    when task completed
    """
    if created:
        return

    if not task.archived:
        return

    advisers_to_notify = task.advisers.exclude(id=task.modified_by.id)

    if not advisers_to_notify.exists():
        return

    for adviser in advisers_to_notify:
        existing_reminder = TaskCompletedReminder.objects.filter(
            task=task,
            adviser=adviser,
        ).first()
        if existing_reminder:
            continue

        reminder = TaskCompletedReminder.objects.create(
            adviser=adviser,
            event=f'{task} completed by {task.modified_by.name}',
            task=task,
        )

        adviser_subscription = TaskCompletedSubscription.objects.filter(
            adviser=adviser,
        ).first()
        if not adviser_subscription:
            return

        if adviser_subscription.email_reminders_enabled is True and is_user_feature_flag_active(
            ADVISER_TASKS_USER_FEATURE_FLAG_NAME,
            adviser,
        ):
            send_task_email(
                adviser=adviser,
                task=task,
                reminders=[reminder],
                update_task=update_task_completed_email_status,
                email_template_class=TaskCompletedEmailTemplate,
            )


def schedule_notify_advisers_task_completed(task, created):
    job = job_scheduler(
        queue_name=LONG_RUNNING_QUEUE,
        function=notify_adviser_completed_task,
        function_args=(task, created),
    )
    logger.info(
        f'Task {job.id} schedule_notify_advisers_task_completed',
    )


def send_task_email(adviser, task, reminders, update_task, email_template_class):
    notify_adviser_by_rq_email(
        adviser=adviser,
        template_identifier=settings.TASK_REMINDER_EMAIL_TEMPLATE_ID,
        context=email_template_class(task).get_context(),
        update_task=update_task,
        reminders=reminders,
    )
