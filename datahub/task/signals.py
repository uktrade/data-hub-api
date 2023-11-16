from django.db.models.signals import m2m_changed, post_delete
from django.dispatch import receiver

from datahub.task.models import InvestmentProjectTask, Task
from datahub.task.tasks import (
    schedule_create_task_assigned_to_me_from_others_subscription_task,
    schedule_create_task_completed_subscription_task,
    schedule_create_task_overdue_subscription_task,
    schedule_create_task_reminder_subscription_task,
)


@receiver(
    post_delete,
    sender=InvestmentProjectTask,
)
def delete_investment_project_task_delete(sender, instance, **kwargs):
    associated_task = Task.objects.filter(pk=instance.task.id).first()
    if instance.task.id:
        if associated_task:
            associated_task.delete()


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
