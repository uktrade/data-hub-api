import uuid
from os import path

from django.conf import settings
from django.db import models

from datahub.core.models import ArchivableModel, BaseModel


class Document(BaseModel, ArchivableModel):
    """General model for keeping track of user uploaded documents."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    path = models.CharField(
        max_length=settings.CHAR_FIELD_MAX_LENGTH,
        unique=True,
    )
    uploaded_on = models.DateTimeField(
        null=True, blank=True
    )
    av_clean = models.BooleanField(default=False)

    @property
    def filename(self):
        return path.basename(self.path)

    def __str__(self):
        return f'Document(filename="{self.filename}", av_clean={self.av_clean})'
