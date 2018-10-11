import uuid
from logging import getLogger

from django.conf import settings
from django.db import models, transaction
from django.utils.timezone import now
from model_utils import Choices

from datahub.core.models import ArchivableModel, BaseModel
from datahub.documents.tasks import virus_scan_document
from datahub.documents.utils import sign_s3_url

logger = getLogger(__name__)


UPLOAD_STATUSES = Choices(
    ('not_virus_scanned', 'Not virus scanned'),
    ('virus_scanning_scheduled', 'Virus scanning scheduled'),
    ('virus_scanning_in_progress', 'Virus scanning in progress'),
    ('virus_scanning_failed', 'Virus scanning failed.'),
    ('virus_scanned', 'Virus scanned'),
    ('deletion_pending', 'Deletion pending'),
)


class Document(BaseModel, ArchivableModel):
    """General model for keeping track of user uploaded documents."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    bucket_id = models.CharField(max_length=settings.CHAR_FIELD_MAX_LENGTH, default='default')
    path = models.CharField(max_length=settings.CHAR_FIELD_MAX_LENGTH)

    uploaded_on = models.DateTimeField(
        null=True, blank=True,
    )
    scan_initiated_on = models.DateTimeField(
        null=True, blank=True,
    )
    scanned_on = models.DateTimeField(
        null=True, blank=True,
    )

    av_clean = models.NullBooleanField(db_index=True)
    av_reason = models.TextField(blank=True)

    status = models.CharField(
        max_length=settings.CHAR_FIELD_MAX_LENGTH,
        choices=UPLOAD_STATUSES,
        default=UPLOAD_STATUSES.not_virus_scanned,
    )

    class Meta:
        unique_together = (
            ('bucket_id', 'path'),
        )

    @property
    def name(self):
        """Model name."""
        return self.path

    def __repr__(self):
        """String repr."""
        return (
            f'Document('
            f'id={self.id!r}, '
            f'bucket_id={self.bucket_id!r}, '
            f'path={self.path!r}, '
            f'uploaded_on={self.uploaded_on!r}, '
            f'scan_initiated_on={self.scan_initiated_on!r}, '
            f'scanned_on={self.scanned_on!r}, '
            f'av_clean={self.av_clean!r}, '
            f'av_reason={self.av_reason!r}, '
            f'status={self.status!r}'
            f')'
        )

    def schedule_av_scan(self):
        """Schedule AV scan."""
        if not self.scan_initiated_on:
            self.mark_scan_scheduled()

            virus_scan_document.apply_async(args=(str(self.pk),))

        return self.status

    def mark_deletion_pending(self):
        """Marks document as scheduled for deletion."""
        return self._update_status(UPLOAD_STATUSES.deletion_pending)

    def mark_as_scanned(self, av_clean, av_reason):
        """Marks document as scanned."""
        self.scanned_on = now()
        self.av_clean = av_clean
        self.av_reason = av_reason
        return self._update_status(UPLOAD_STATUSES.virus_scanned)

    def mark_scan_scheduled(self):
        """Marks document scan has been scheduled."""
        self.uploaded_on = now()
        return self._update_status(UPLOAD_STATUSES.virus_scanning_scheduled)

    def mark_scan_initiated(self):
        """Marks document that scan has been initiated."""
        self.scan_initiated_on = now()
        return self._update_status(UPLOAD_STATUSES.virus_scanning_in_progress)

    def mark_scan_failed(self, reason):
        """Marks document that scan has failed."""
        self.av_reason = reason
        return self._update_status(UPLOAD_STATUSES.virus_scanning_failed)

    def _update_status(self, status):
        self.status = status
        self.save()
        return self.status

    def get_signed_url(self, allow_unsafe=False):
        """
        Generate pre-signed download URL.

        URL is generated when either file has passed virus scanning (av_clean=True)
        or allow_unsafe is set.
        """
        if self.av_clean or allow_unsafe:
            return sign_s3_url(
                self.bucket_id,
                self.path,
            )
        return None

    def get_signed_upload_url(self):
        """Generate pre-signed upload URL."""
        assert self.scan_initiated_on is None

        return sign_s3_url(
            self.bucket_id,
            self.path,
            method='put_object',
        )


class EntityDocumentManager(models.Manager):
    """Base entity document manager."""

    @transaction.atomic
    def create(self, original_filename, **kwargs):
        """Create entity document along with the corresponding Document."""
        document_pk = uuid.uuid4()
        document = Document(
            pk=document_pk,
            bucket_id=self.model.BUCKET,
            path=self._create_document_path(document_pk, original_filename),
            status=UPLOAD_STATUSES.not_virus_scanned,
        )
        document.save()
        return super().create(
            document=document,
            original_filename=original_filename,
            **kwargs,
        )

    def get_queryset(self):
        """Exclude objects with document having deletion pending as status."""
        return super().get_queryset().exclude(document__status=UPLOAD_STATUSES.deletion_pending)

    def include_objects_deletion_pending(self):
        """
        Gets query set for all objects.

        (including objects with document having deletion pending as status).
        """
        return super().get_queryset()

    def _create_document_path(self, document_pk, original_filename):
        """Create document path."""
        today = now().strftime('%Y-%m-%d')
        return f'{self.model._meta.model_name}/{today}/{document_pk}/{original_filename}'


class AbstractEntityDocumentModel(BaseModel):
    """
    Base document model.

    Entity document having its corresponding document with status=UPLOAD_STATUSES_deletion_pending
    should not be included in the responses to clients. This is achieved in EntityDocumentManager,
    where default queryset excludes entity documents if their corresponding document has
    deletion_pending status.

    If access to deletion_pending entity documents is needed, then manager's
    include_objects_deletion_pending method, that returns untouched queryset, should be used.
    """

    BUCKET = 'default'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    original_filename = models.CharField(max_length=settings.CHAR_FIELD_MAX_LENGTH)
    document = models.OneToOneField(Document, on_delete=models.CASCADE)

    objects = EntityDocumentManager()

    class Meta:
        abstract = True
