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

    def __str__(self):
        """Admin displayed human readable name."""
        return self.title


class BaseTaskType(BaseModel):
    """
    Base task model for task types to have a FK to task
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='%(app_label)s_%(class)s',
    )

    class Meta:
        abstract = True


@reversion.register_base_model()
class InvestmentProjectTask(BaseTaskType):
    """Representation as an investment project task"""

    investment_project = models.ForeignKey(
        InvestmentProject,
        on_delete=models.CASCADE,
        related_name='task',
    )

    def __str__(self):
        """Admin displayed human readable name."""
        return f'Investment project - {self.task.title}'
