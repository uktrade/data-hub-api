from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from datahub.task.models import InvestmentProjectTask, Task
from datahub.task.tasks import schedule_create_task_reminder_subscription_task


@receiver(
    post_save,
    sender=Task,
    dispatch_uid='set_task_reminder_subscription_after_task_post_save',
)
def set_task_reminder_subscription_after_task_post_save(sender, instance, **kwargs):
    """
    Checks to see if an Adviser has a Task Reminder Subscription. If they do not
    then a subscription for the Adviser will be created
    """
    print('******** Hello I received a thing')
    schedule_create_task_reminder_subscription_task(instance)
