import uuid

from django.conf import settings
from django.db import models

from datahub.core.models import BaseModel

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class FeatureFlag(BaseModel):
    """Feature flag.

    It keeps the status of features - whether one is enabled or disabled.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    code = models.CharField(unique=True, max_length=MAX_LENGTH)
    description = models.TextField(blank=True)
    is_active = models.BooleanField()

    class Meta:
        ordering = ('code',)

    def __str__(self):
        """Human readable representation."""
        return f'{self.code} - {self.is_active}'
