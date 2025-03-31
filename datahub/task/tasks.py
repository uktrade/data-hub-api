import datetime
import logging

from django.apps import apps
from django.conf import settings
from django.utils import timezone
from django_pglocks import advisory_lock

from datahub.company.models import Advisor
from datahub.core.queues.constants import HALF_DAY_IN_SECONDS
from datahub.core.queues.job_scheduler import job_scheduler
from datahub.core.queues.scheduler import LONG_RUNNING_QUEUE
from datahub.reminder.models import (
    TaskAmendedByOthersReminder,
    TaskAmendedByOthersSubscription,
    TaskAssignedToMeFromOthersReminder,
    TaskAssignedToMeFromOthersSubscription,
    TaskCompletedReminder,
    TaskCompletedSubscription,
    TaskDeletedByOthersReminder,
    TaskDeletedByOthersSubscription,
    TaskOverdueReminder,
    TaskOverdueSubscription,
    UpcomingTaskReminder,
    UpcomingTaskReminderSubscription,
)
from datahub.reminder.tasks import notify_adviser_by_rq_email
from datahub.task.emails import (
    TaskAmendedByOthersEmailTemplate,
    TaskAssignedToOthersEmailTemplate,
    TaskCompletedEmailTemplate,
    TaskDeletedByOthersEmailTemplate,
    TaskOverdueEmailTemplate,
    UpcomingTaskEmailTemplate,
)
from datahub.task.models import Task

logger = logging.getLogger(__name__)


def schedule_advisers_added_to_task(task, adviser_ids):
    for adviser_id in adviser_ids:
        schedule_create_task_reminder_subscription_task(adviser_id)
        schedule_create_task_assigned_to_me_from_others_subscription_task(task, adviser_id)
        schedule_create_task_overdue_subscription_task(adviser_id)
        schedule_create_task_completed_subscription_task(adviser_id)
        schedule_create_task_archived_subscription_task(adviser_id)
        schedule_create_task_amended_by_others_subscription_task(adviser_id)


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
    """Creates a task reminder subscription for an adviser if the adviser doesn't have
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
    """Creates a reminder and sends an email if required.

    If a reminder has already been sent on the same day, then do nothing.
    """
    if _has_existing_upcoming_task_reminder(task, adviser, current_date):
        return

    reminder = UpcomingTaskReminder.objects.create(
        adviser=adviser,
        event=f'{task.reminder_days} days left to task due',
        task=task,
    )

    if send_email:
        send_task_email(
            adviser=adviser,
            task=task,
            reminder=reminder,
            update_task=update_task_reminder_email_status,
            email_template_class=UpcomingTaskEmailTemplate,
        )
    else:
        logger.info(
            f'No email for UpcomingTaskReminder with id {reminder.id} sent to adviser '
            f'{adviser.id} for task {task.id}, as email reminders are turned off in their '
            'subscription',
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

    logger.info(
        'Task update_task_reminder_email_status completed, setting '
        f'email_notification_id to {email_notification_id} for reminder_ids {reminder_ids}',
    )


def update_task_overdue_reminder_email_status(email_notification_id, reminder_ids):
    reminders = TaskOverdueReminder.all_objects.filter(id__in=reminder_ids)
    for reminder in reminders:
        reminder.email_notification_id = email_notification_id
        reminder.save()

    logger.info(
        'Task update_task_overdue_reminder_email_status completed, setting '
        f'email_notification_id to {email_notification_id} for reminder_ids {reminder_ids}',
    )


def update_task_assigned_to_me_from_others_email_status(email_notification_id, reminder_ids):
    reminders = TaskAssignedToMeFromOthersReminder.all_objects.filter(id__in=reminder_ids)
    for reminder in reminders:
        reminder.email_notification_id = email_notification_id
        reminder.save()

    logger.info(
        'Task update_task_assigned_to_me_from_others_email_status completed, setting '
        f'email_notification_id to {email_notification_id} for reminder_ids {reminder_ids}',
    )


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
    """Creates a task reminder subscription for an adviser if the adviser doesn't have
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
    """Send a notification to the adviser added to the task
    """
    if adviser_id == task.created_by.id:
        return
    if adviser_id == task.modified_by.id:
        return
    adviser = Advisor.objects.filter(id=str(adviser_id)).first()

    if not adviser:
        return

    reminder = TaskAssignedToMeFromOthersReminder.objects.create(
        adviser=adviser,
        event=f'{task} assigned to me by {task.modified_by.name}',
        task=task,
    )
    task_subscription = create_task_assigned_to_me_from_others_subscription(adviser)

    if task_subscription.email_reminders_enabled:
        send_task_email(
            adviser=adviser,
            task=task,
            reminder=reminder,
            update_task=update_task_assigned_to_me_from_others_email_status,
            email_template_class=TaskAssignedToOthersEmailTemplate,
        )
    else:
        logger.info(
            f'No email for TaskAssignedToMeFromOthersReminder with id {reminder.id} sent to '
            f'adviser {adviser.id} for task {task.id}, as email reminders are turned off in their '
            'subscription',
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
    """Creates a task overdue subscription for an adviser if the adviser doesn't have
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

    logger.info(
        'Task update_task_completed_email_status completed, setting '
        f'email_notification_id to {email_notification_id} for reminder_ids {reminder_ids}',
    )


def update_task_deleted_email_status(email_notification_id, reminder_ids):
    reminders = TaskDeletedByOthersReminder.all_objects.filter(id__in=reminder_ids)
    for reminder in reminders:
        reminder.email_notification_id = email_notification_id
        reminder.save()

    logger.info(
        'Task update_task_deleted_email_status completed, setting '
        f'email_notification_id to {email_notification_id} for reminder_ids {reminder_ids}',
    )


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
    """Creates a task completed subscription for an adviser if the adviser doesn't have
    a subscription already.
    """
    if not TaskCompletedSubscription.objects.filter(
        adviser_id=adviser_id,
    ).first():
        TaskCompletedSubscription.objects.create(
            adviser_id=adviser_id,
            email_reminders_enabled=True,
        )


def schedule_create_task_archived_subscription_task(adviser_id):
    job = job_scheduler(
        queue_name=LONG_RUNNING_QUEUE,
        function=create_task_deleted_by_others_subscription,
        function_args=(adviser_id,),
    )
    logger.info(
        f'Task {job.id} create_task_archived_subscription',
    )


def create_task_deleted_by_others_subscription(adviser_id):
    """Creates a task deleted/archived by others subscription for an adviser if the adviser doesn't
    have a subscription already.
    """
    if not TaskDeletedByOthersSubscription.objects.filter(
        adviser_id=adviser_id,
    ).first():
        TaskDeletedByOthersSubscription.objects.create(
            adviser_id=adviser_id,
            email_reminders_enabled=True,
        )


def notify_adviser_archived_completed_or_amended_task(
    task,
    created,
    adviser_ids_pre_m2m_change=None,
):
    """Send a notification to all advisers, excluding the adviser who amended,
    archived/deleted or completed the task.
    After a task status has been set to completed:
    - it can no longer be edited
    - it can be archived/deleted
    - The TaskCompletedReminder should be send.
    After a task has been archived/deleted:
    - it can no longer be edited (including changing the status)
    - it **can** be undeleted/unarchived
    - The TaskDeletedByOthersReminder should be send.
    - No other notifications should be send once a Task has been archived/deleted.
    After a task has been amended:
    - The TaskAmmendedByOthersReminder should be send.

    task: Task
    created: true or false depending on whether the task has been created or updated.
    adviser_ids_pre_m2m_change: values of adviser ids that have been updated before the
    m2m_change. Used for amended by others only.
    """
    if created:
        return

    if task.archived:
        notify_advisers_of_task(
            task,
            None,
            TaskDeletedByOthersReminder,
            TaskDeletedByOthersSubscription,
            TaskDeletedByOthersEmailTemplate,
            update_task_completed_email_status,
        )
        return

    if task.status is Task.Status.COMPLETE:
        notify_advisers_of_task(
            task,
            None,
            TaskCompletedReminder,
            TaskCompletedSubscription,
            TaskCompletedEmailTemplate,
            update_task_completed_email_status,
        )
        return

    notify_advisers_of_task(
        task,
        adviser_ids_pre_m2m_change,
        TaskAmendedByOthersReminder,
        TaskAmendedByOthersSubscription,
        TaskAmendedByOthersEmailTemplate,
        update_task_amended_by_others_email_status,
    )
    return


def notify_advisers_of_task(
    task,
    adviser_ids_pre_m2m_change,
    reminder_class,
    subscription_class,
    email_template_class,
    update_task_function,
):
    """_summary_
    For all advisers of the task, excluding the adviser who performed this action:
        - Create a reminder
        - Send an email notification provided the adviser has a subscription setup.

    Args:
        task (_type_): Task to notify advisers for.
        reminder_class (BaseReminder): Reminder class to be used.
        subscription_class (BaseSubscription): Subscription class to be used.
        email_template_class (EmailTemplate): Email Template class to be used.

    """
    if adviser_ids_pre_m2m_change is None:
        advisers_to_notify = task.advisers.exclude(
            id=task.modified_by.id,
        )
    else:
        advisers_to_notify = task.advisers.filter(id__in=adviser_ids_pre_m2m_change).exclude(
            id=task.modified_by.id,
        )

    if not advisers_to_notify.exists():
        return

    for adviser in advisers_to_notify:
        existing_reminder = apps.get_model('reminder', reminder_class.__name__).objects.filter(
            task=task,
            adviser=adviser,
        ).first()
        if existing_reminder:
            continue
        reminder = apps.get_model('reminder', reminder_class.__name__).objects.create(
            adviser=adviser,
            event=f'{task} {reminder_class.__name__} by {task.modified_by.name}',
            task=task,
        )

        adviser_subscription = apps.get_model(
            'reminder',
            subscription_class.__name__,
        ).objects.filter(
            adviser=adviser,
        ).first()
        if not adviser_subscription:
            return

        if adviser_subscription.email_reminders_enabled:
            send_task_email(
                adviser=adviser,
                task=task,
                reminder=reminder,
                update_task=update_task_function,
                email_template_class=email_template_class,
            )
        else:
            logger.info(
                f'No email for {reminder_class.__name__} with id {reminder.id} sent to adviser '
                f'{adviser.id} for task {task.id}, as email reminders are turned off in their '
                'subscription',
            )


def schedule_notify_advisers_task_archived_completed_or_amended(
    task,
    created,
    adviser_ids_pre_m2m_change,
):
    job = job_scheduler(
        queue_name=LONG_RUNNING_QUEUE,
        function=notify_adviser_archived_completed_or_amended_task,
        function_args=(task, created, adviser_ids_pre_m2m_change),
    )
    logger.info(
        f'Task {job.id} schedule_notify_advisers_task_archived_completed_or_amended',
    )


def update_task_amended_by_others_email_status(email_notification_id, reminder_ids):
    reminders = TaskAmendedByOthersReminder.all_objects.filter(id__in=reminder_ids)
    for reminder in reminders:
        reminder.email_notification_id = email_notification_id
        reminder.save()

    logger.info(
        'Task update_task_amended_by_others_email_status completed'
        f'email_notification_id to {email_notification_id} and reminder_ids set to {reminder_ids}',
    )


def create_task_amended_by_others_subscription(adviser_id):
    """Creates a task amended by others subscription for an adviser if the adviser doesn't have
    a subscription already.
    """
    if not TaskAmendedByOthersSubscription.objects.filter(
        adviser_id=adviser_id,
    ).first():
        TaskAmendedByOthersSubscription.objects.create(
            adviser_id=adviser_id,
            email_reminders_enabled=True,
        )


def schedule_create_task_amended_by_others_subscription_task(adviser_id):
    job = job_scheduler(
        queue_name=LONG_RUNNING_QUEUE,
        function=create_task_amended_by_others_subscription,
        function_args=(adviser_id,),
    )
    logger.info(
        f'Task {job.id} create_task_amended_by_others_subscription',
    )


def send_task_email(adviser, task, reminder, update_task, email_template_class):
    logger.info(
        f'Sending an email for Task {task.id} and reminder {reminder.id} to adviser {adviser.id}',
    )

    notify_adviser_by_rq_email(
        adviser=adviser,
        template_identifier=settings.TASK_REMINDER_EMAIL_TEMPLATE_ID,
        context=email_template_class(task).get_context(),
        update_task=update_task,
        reminders=[reminder],
    )


def schedule_reminders_tasks_overdue():
    job = job_scheduler(
        queue_name=LONG_RUNNING_QUEUE,
        function=generate_reminders_tasks_overdue,
        job_timeout=HALF_DAY_IN_SECONDS,
        max_retries=5,
        retry_backoff=True,
        retry_intervals=30,
    )
    logger.info(
        f'Task {job.id} generate_reminders_tasks_overdue scheduled',
    )
    return job


def generate_reminders_tasks_overdue():
    """Generate reminders for all advisers on overdue tasks.
    Do not send reminders if task is archived or status is complete.
    """
    with advisory_lock(
        'generate_reminders_tasks_overdue',
        wait=False,
    ) as acquired:
        if not acquired:
            logger.info(
                'Reminders for tasks overdue are already being processed by another worker.',
            )
            return
        now = timezone.now()
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        tasks = Task.objects.filter(due_date=yesterday).exclude(archived=True).exclude(
            status=Task.Status.COMPLETE,
        )
        for task in tasks:
            # Get all active advisers assigned to the task
            active_advisers = task.advisers.filter(is_active=True)
            for adviser in active_advisers:
                # Get subscription to know if emails are needed
                adviser_subscription = TaskOverdueSubscription.objects.filter(
                    adviser=adviser,
                ).first()
                if adviser_subscription:
                    create_tasks_overdue_reminder(
                        task,
                        adviser,
                        adviser_subscription.email_reminders_enabled,
                        now,
                    )

        logger.info(
            'Task generate_reminders_tasks_overdue completed',
        )
        return tasks


def create_tasks_overdue_reminder(
    task,
    adviser,
    send_email,
    current_date,
):
    """Creates a reminder and sends an email if required.

    If a reminder has already been sent on the same day, then do nothing.
    """
    if _has_existing_tasks_overdue_reminder(task, adviser, current_date):
        return

    reminder = TaskOverdueReminder.objects.create(
        adviser=adviser,
        event=f'{task.title} is now overdue',
        task=task,
    )

    if send_email:
        send_task_email(
            adviser=adviser,
            task=task,
            reminder=reminder,
            update_task=update_task_overdue_reminder_email_status,
            email_template_class=TaskOverdueEmailTemplate,
        )
    else:
        logger.info(
            f'No email for TaskOverdueReminder with id {reminder.id} sent to adviser '
            f'{adviser.id} for task {task.id}, as email reminders are turned off in their '
            'subscription',
        )

    return reminder


def _has_existing_tasks_overdue_reminder(task, adviser, current_date):
    return TaskOverdueReminder.objects.filter(
        task=task,
        adviser=adviser,
        created_on__month=current_date.month,
        created_on__year=current_date.year,
    ).exists()
