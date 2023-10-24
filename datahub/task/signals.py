from django.db.models.signals import m2m_changed, post_delete, pre_save, post_save
from django.dispatch import receiver

from datahub.task.models import InvestmentProjectTask, Task
from datahub.task.tasks import (
    schedule_create_task_assigned_to_me_from_others_subscription_task,
    schedule_create_task_reminder_subscription_task,
    send_notification_task_assigned_from_others_email_task,
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


# @receiver(
#     m2m_changed,
#     sender=Task.advisers.through,
#     dispatch_uid='set_task_reminder_subscription_after_task_post_save',
# )
# def set_task_reminder_subscription_after_task_post_save(sender, instance, **kwargs):
#     """
#     Checks to see if a Task has any advisers. If there are advisers then this is
#     passed to the task for processing to add task reminder subscriptions
#     """
#     advisers = instance.advisers.all()
#     for adviser in advisers:
#         schedule_create_task_reminder_subscription_task(adviser)
#         schedule_create_task_assigned_to_me_from_others_subscription_task(adviser)


@receiver(
    m2m_changed,
    sender=Task.advisers.through,
    # dispatch_uid='send_task_assigned_from_others_email',
)
def send_task_assigned_from_others_email(sender, **kwargs):
    """
    Checks to see if a Task has any advisers. If there are advisers then this is
    passed to the task for processing to add task reminder subscriptions
    """
    task = kwargs.pop('instance', None)
    pk_set = kwargs.pop('pk_set', None)
    action = kwargs.pop('action', None)
    print('*****************', action)
    for adviser in pk_set:
        print('aaaaaaaa', adviser)
        send_notification_task_assigned_from_others_email_task(task, adviser)
