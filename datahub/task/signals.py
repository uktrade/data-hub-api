from django.db.models.signals import post_delete
from django.dispatch import receiver

from datahub.task.models import InvestmentProjectTask, Task


@receiver(
    post_delete,
    sender=InvestmentProjectTask,
)
def delete_investment_project_task_delete(sender, instance, **kwargs):
    if instance.task.id:
        associated_task = Task.objects.filter(pk=instance.task.id).first()
        if associated_task:
            associated_task.delete()
