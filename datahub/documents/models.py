import uuid
from logging import getLogger
from os import path

from django.conf import settings
from django.db import models, transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver

from datahub.core.models import ArchivableModel, BaseModel
from datahub.core.utils import delete_s3_obj, sign_s3_url, submit_to_thread_pool

logger = getLogger(__name__)


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
    scan_initiated_on = models.DateTimeField(
        null=True, blank=True,
    )
    scanned_on = models.DateTimeField(
        null=True, blank=True,
    )
    av_clean = models.NullBooleanField(db_index=True)

    @property
    def filename(self):
        """Shortcut for getting a filename."""
        return path.basename(self.path)

    @property
    def name(self):
        """Model name."""
        return self.path

    def generate_signed_url(self):
        """Generate pre-signed download URL, but only if doc is AV clean."""
        if self.av_clean:
            return sign_s3_url(settings.DOCUMENTS_BUCKET, self.path)

    def generate_signed_upload_url(self):
        """Generate pre-signed upload URL."""
        return sign_s3_url(
            settings.DOCUMENTS_BUCKET, self.path, method='put_object',
        )

    @property
    def s3_bucket(self):
        """The S3 bucket where this document is stored."""
        return settings.DOCUMENTS_BUCKET

    @property
    def s3_key(self):
        """The S3 key corresponding to this bucket."""
        return self.path

    def __str__(self):
        """String repr."""
        return f'Document(filename="{self.filename}", av_clean={self.av_clean})'


@receiver(post_delete, sender=Document)
def document_post_delete(sender, **kwargs):
    """Handle document delete."""
    instance = kwargs['instance']
    if instance.uploaded_on is None:
        return

    # grab only needed vars for closure, so instance can go out-of-scope
    bucket = instance.s3_bucket
    key = instance.s3_key

    def delete_document():
        delete_s3_obj(bucket, key)

    transaction.on_commit(
        lambda: submit_to_thread_pool(delete_document)
    )
