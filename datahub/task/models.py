import uuid

from django.conf import settings
from django.db import models

from datahub.company.models import Advisor

from datahub.core import reversion

from datahub.core.models import ArchivableModel, BaseModel
from datahub.investment.project.models import InvestmentProject

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


@reversion.register_base_model()
class Task(ArchivableModel, BaseModel):
    """Representation of a task."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    title = models.CharField(max_length=MAX_LENGTH)
    description = models.TextField(blank=True, default='')
    due_date = models.DateField(null=True, blank=True)
    reminder_days = models.SmallIntegerField(null=True, blank=True)
    email_reminders_enabled = models.BooleanField(default=False)
    advisers = models.ManyToManyField(
        Advisor,
        related_name='+',
    )


@reversion.register_base_model()
class InvestmentProjectTask(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='investment_project',
    )
    investment_project = models.ForeignKey(
        InvestmentProject,
        on_delete=models.PROTECT,
        related_name='task',
    )
