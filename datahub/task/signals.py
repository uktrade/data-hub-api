from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver

from datahub.task.models import Task
from datahub.task.tasks import (
    schedule_advisers_added_to_task,
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
        schedule_advisers_added_to_task(
            adviser_ids=pk_set,
            task=task,
        )


@receiver(
    post_save,
    sender=Task,
    dispatch_uid='save_task',
)
def save_task(sender, instance, created, **kwargs):
    """
    Triggers when a task is saved
    """
    # As the adviser field is an m2m field, it will never contain the changed value in this signal.
    # Adviser changes are reflected in a separate m2m changed signal. As the scheduled jobs run in
    # a queue, there can be a mismatch between the advisers in this signal and the advisers
    # available when the queue function runs. This loads the advisers into a list as it is before
    # any m2m changes are triggered by the m2m signal
    adviser_ids_pre_m2m_change = list(instance.advisers.all().values_list('id', flat=True))

    schedule_notify_advisers_task_completed(instance, created)
    schedule_notify_advisers_task_amended_by_others(instance, created, adviser_ids_pre_m2m_change)
