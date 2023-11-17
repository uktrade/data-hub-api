from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver

from datahub.task.models import Task
from datahub.task.tasks import (
    schedule_create_task_amended_by_others_subscription_task,
    schedule_create_task_assigned_to_me_from_others_subscription_task,
    schedule_create_task_completed_subscription_task,
    schedule_create_task_overdue_subscription_task,
    schedule_create_task_reminder_subscription_task,
    schedule_notify_advisers_task_amended_by_others,
    schedule_notify_advisers_task_completed,
)


@receiver(
    m2m_changed,
    sender=Task.advisers.through,
    dispatch_uid='set_task_subscriptions_and_schedule_notifications',
)
def set_task_subscriptions_and_schedule_notifications(sender, **kwargs):
    """
    Checks to see if a Task has any advisers. If there are advisers then this is
    passed to the task for processing to add task reminder subscriptions
    """
    task = kwargs.pop('instance', None)
    pk_set = kwargs.pop('pk_set', None)
    action = kwargs.pop('action', None)
    if action == 'post_add' and pk_set is not None and task is not None:
        for adviser_id in pk_set:
            schedule_create_task_reminder_subscription_task(adviser_id)
            schedule_create_task_assigned_to_me_from_others_subscription_task(task, adviser_id)
            schedule_create_task_overdue_subscription_task(adviser_id)
            schedule_create_task_completed_subscription_task(adviser_id)
            schedule_create_task_amended_by_others_subscription_task(adviser_id)


@receiver(
    post_save,
    sender=Task,
    dispatch_uid='save_task',
)
def save_task(sender, instance, created, **kwargs):
    """
    Triggers when a task is saved
    """
    schedule_notify_advisers_task_completed(instance, created)
    schedule_notify_advisers_task_amended_by_others(instance, created)
