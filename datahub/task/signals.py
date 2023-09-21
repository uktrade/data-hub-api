from django.db.models.signals import m2m_changed, post_delete
from django.dispatch import receiver

from datahub.task.models import InvestmentProjectTask, Task
from datahub.task.tasks import schedule_create_task_reminder_subscription_task


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
    dispatch_uid='set_task_reminder_subscription_after_task_post_save',
)
def set_task_reminder_subscription_after_task_post_save(sender, instance, **kwargs):
    """
    Checks to see if a Task has any advisers. If there are advisers then this is
    passed to the task for processing to add task reminder subscriptions
    """
    if instance.advisers.all().count():
        schedule_create_task_reminder_subscription_task(instance.advisers.all())
