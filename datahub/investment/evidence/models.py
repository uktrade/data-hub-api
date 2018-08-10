"""Investment project evidence models."""


import uuid

from django.conf import settings
from django.db import models

from datahub.core.models import BaseModel
from datahub.documents.models import AbstractEntityDocumentModel

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class Evidence(BaseModel):
    """Evidence model."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    investment_project = models.ForeignKey(
        'investment.InvestmentProject', on_delete=models.CASCADE, related_name='evidence'
    )

    name = models.CharField(max_length=MAX_LENGTH)

    def __str__(self):
        """Human readable representation of the object."""
        return f'{self.investment_project.name} - {self.name}'


class EvidenceDocument(AbstractEntityDocumentModel):
    """Evidence Document model."""

    BUCKET = 'investment'

    evidence = models.ForeignKey(
        Evidence,
        related_name='documents',
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = 'investment project evidence document'

    def __str__(self):
        """Human readable representation of the object."""
        return f'{self.evidence.name} - {self.original_filename}'
