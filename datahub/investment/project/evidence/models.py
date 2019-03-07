"""Investment project evidence models."""

from django.db import models
from rest_framework.reverse import reverse

from datahub.core.models import BaseConstantModel
from datahub.core.utils import StrEnum
from datahub.documents.models import AbstractEntityDocumentModel


class EvidenceTag(BaseConstantModel):
    """Evidence tag."""


class EvidenceDocumentPermission(StrEnum):
    """
    Permission codename constants.

    (Defined here rather than in permissions to avoid an import of that module.)


    The following codenames mean that the user can read, change, add or delete any type of
    evidence document:

    view_all_evidencedocument
    change_all_evidencedocument
    add_all_evidencedocument
    delete_evidencedocument


    The following codenames mean that the user can only read, change and add evidence
    documents for investment projects that they are associated with:

    view_associated_evidencedocument
    change_associated_evidencedocument
    add_associated_evidencedocument
    delete_associated_evidencedocument

    An associated project has the same meaning that it does in investment projects (that is a
    project that was created by an adviser in the same team, or an adviser in the same team has
    been linked to the project).

    Note that permissions on other models are independent of permissions on evidence documents.
    Also note that if both *_all_* and *_associated_* permissions are
    assigned to the same user,  the *_all_* permission will be the effective one.
    """

    view_all = 'view_all_evidencedocument'
    view_associated = 'view_associated_evidencedocument'
    change_all = 'change_all_evidencedocument'
    change_associated = 'change_associated_evidencedocument'
    add_all = 'add_all_evidencedocument'
    add_associated = 'add_associated_evidencedocument'
    delete_all = 'delete_all_evidencedocument'
    delete_associated = 'delete_associated_evidencedocument'


class EvidenceDocument(AbstractEntityDocumentModel):
    """Evidence Document model."""

    BUCKET = 'investment'

    investment_project = models.ForeignKey(
        'investment.InvestmentProject',
        on_delete=models.CASCADE,
        related_name='evidence_documents',
    )
    comment = models.TextField(blank=True)

    tags = models.ManyToManyField(
        EvidenceTag,
        related_name='+',
    )

    class Meta:
        verbose_name = 'investment project evidence document'
        permissions = (
            (
                EvidenceDocumentPermission.add_associated.value,
                'Can add evidence document for associated investment projects',
            ),
            (
                EvidenceDocumentPermission.change_associated.value,
                'Can change evidence document for associated investment projects',
            ),
            (
                EvidenceDocumentPermission.delete_associated.value,
                'Can delete evidence document for associated investment projects',
            ),
            (
                EvidenceDocumentPermission.view_associated.value,
                'Can view evidence document for associated investment projects',
            ),
        )
        default_permissions = (
            'add_all',
            'change_all',
            'delete_all',
            'view_all',
        )

    def __str__(self):
        """Human readable representation of the object."""
        return f'{self.investment_project.name} - {self.original_filename}'

    @property
    def url(self):
        """Returns URL to download endpoint."""
        return reverse(
            'api-v3:investment:evidence-document:document-item-download',
            kwargs={
                'project_pk': self.investment_project.pk,
                'entity_document_pk': self.pk,
            },
        )
