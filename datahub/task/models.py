import uuid

from django.conf import settings
from django.db import models

from datahub.company.models import Advisor

from datahub.core import reversion

from datahub.core.models import ArchivableModel, BaseModel

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


@reversion.register_base_model()
class Task(ArchivableModel, BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    title = models.CharField(max_length=MAX_LENGTH)
    description = models.TextField(blank=True, default='')
    due_date = models.DateField(null=True, blank=True)
    reminder_days = models.SmallIntegerField(null=True, blank=True)
    email_reminders_enabled = models.BooleanField(default=False)
    advisers = models.ManyToManyField(
        Advisor,
        blank=False,
        related_name='+',
    )
