import uuid

from datetime import timedelta

from django.conf import settings
from django.db import models


from datahub.company.models import Advisor
from datahub.company.models.company import Company

from datahub.core import reversion
from datahub.core.models import ArchivableModel, BaseModel
from datahub.core.utils import get_front_end_url, StrEnum
from datahub.interaction.models import Interaction
from datahub.investment.project.models import InvestmentProject

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class TaskPermission(StrEnum):
    """Permission codename constants."""

    view_task = 'view_task'


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
    reminder_date = models.DateField(null=True, blank=True, editable=False)
    investment_project = models.ForeignKey(
        InvestmentProject,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='task_investment_project',
    )
    company = models.ForeignKey(
        Company,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='task_company',
    )
    interaction = models.ForeignKey(
        Interaction,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='task_interaction',
    )

    # override the save method and calculate reminder_date
    def save(self, *args, **kwargs):
        if self.due_date and self.reminder_days:
            self.reminder_date = self.due_date - timedelta(days=self.reminder_days)
        super().save(*args, **kwargs)

    def __str__(self):
        """Admin displayed human readable name."""
        return self.title

    def get_absolute_url(self):
        """URL to the object in the Data Hub internal front end."""
        return get_front_end_url(self)

    def get_company(self):
        """
        Get the company from the available foreign keys
        """
        if self.investment_project:
            return self.investment_project.investor_company
        if self.company:
            return self.company
        if self.interaction:
            return self.interaction.company
        return None
