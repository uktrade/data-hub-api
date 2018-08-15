"""Investment project evidence models."""

from django.db import models

from datahub.core.models import BaseConstantModel
from datahub.documents.models import AbstractEntityDocumentModel


class EvidenceTag(BaseConstantModel):
    """Evidence tag."""


class EvidenceDocument(AbstractEntityDocumentModel):
    """Evidence Document model."""

    BUCKET = 'investment'

    investment_project = models.ForeignKey(
        'investment.InvestmentProject',
        on_delete=models.CASCADE,
        related_name='evidence_documents'
    )
    comment = models.TextField(blank=True)

    tags = models.ManyToManyField(
        EvidenceTag,
        related_name='+',
    )

    class Meta:
        verbose_name = 'investment project evidence document'

    def __str__(self):
        """Human readable representation of the object."""
        return f'{self.investment_project.name} - {self.original_filename}'
