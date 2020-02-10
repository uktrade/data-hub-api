from django.db import models


class UserEventType(models.TextChoices):
    """User event types."""

    SEARCH_EXPORT = ('search_export', 'Exported search results')
    PROPOSITION_DOCUMENT_DELETE = ('proposition_document_delete', 'Deleted proposition document')
    EVIDENCE_DOCUMENT_DELETE = ('evidence_document_delete', 'Deleted evidence document')
