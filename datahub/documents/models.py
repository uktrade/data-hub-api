import uuid
from os import path

from django.conf import settings
from django.db import models

from datahub.core.models import ArchivableModel, BaseModel
from datahub.core.utils import sign_s3_url


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
    av_clean = models.NullBooleanField()

    @property
    def filename(self):
        """Shortcut for getting a filename."""
        return path.basename(self.path)

    @property
    def name(self):
        """Model name."""
        return self.path

    def generate_signed_url(self):
        """Generate pre-signed download URL."""
        return sign_s3_url(settings.DOCUMENTS_BUCKET, self.path)

    def generate_signed_upload_url(self):
        """Generate pre-signed upload URL."""
        return sign_s3_url(settings.DOCUMENTS_BUCKET, self.path, method='put_object')

    def __str__(self):
        """String repr."""
        return f'Document(filename="{self.filename}", av_clean={self.av_clean})'
