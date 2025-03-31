import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from datahub.core import reversion

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


@reversion.register_base_model()
class IngestedFile(models.Model):  # noqa: DJ008
    """Model to track which Company Activity data source files have been ingested already."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    created_on = models.DateTimeField(
        auto_now_add=True,
        help_text='DateTime the instance was created',
    )
    filepath = models.CharField(
        max_length=MAX_LENGTH,
        help_text=('The S3 object path including prefix of the ingested file'),
    )
    file_created = models.DateTimeField(
        default=timezone.now,
        help_text='DateTime the ingested file was last modified in S3',
    )
