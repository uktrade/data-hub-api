"""Investment project evidence models."""


import uuid

from django.conf import settings
from django.db import models

from datahub.core.models import BaseModel
from datahub.core.utils import StrEnum
from datahub.documents.models import AbstractEntityDocumentModel

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class EvidenceGroupPermission(StrEnum):
    """
    Permission codename constants.

    (Defined here rather than in permissions to avoid an import of that module.)


    The following codenames mean that the user can read, change, add or delete any type of
    evidence group:

    read_all_evidencegroup
    change_all_evidencegroup
    add_all_evidencegroup
    delete_evidencegroup


    The following codenames mean that the user can only read, change and add evidence groups for
    investment projects that they are associated with:

    read_associated_evidencegroup
    change_associated_evidencegroup
    add_associated_evidencegroup

    An associated project has the same meaning that it does in investment projects (that is a
    project that was created by an adviser in the same team, or an adviser in the same team has
    been linked to the project).

    Note that permissions on other models are independent of permissions on evidence groups. Also
    note that if both *_all_* and *_associated_* permissions are assigned to the
    same user,  the *_all_* permission will be the effective one.
    """

    read_all = 'read_all_evidencegroup'
    read_associated_investmentproject = 'read_associated_evidencegroup'
    change_all = 'change_all_evidencegroup'
    change_associated_investmentproject = 'change_associated_evidencegroup'
    add_all = 'add_all_evidencegroup'
    add_associated_investmentproject = 'add_associated_evidencegroup'
    delete = 'delete_evidencegroup'


class EvidenceGroup(BaseModel):
    """Evidence Group model."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    investment_project = models.ForeignKey(
        'investment.InvestmentProject', on_delete=models.CASCADE, related_name='evidence'
    )

    name = models.CharField(max_length=MAX_LENGTH)

    class Meta:
        permissions = (
            (
                EvidenceGroupPermission.read_all.value,
                'Can read all proposition'
            ),
            (
                EvidenceGroupPermission.read_associated_investmentproject.value,
                'Can read evidence group for associated investment projects'
            ),
            (
                EvidenceGroupPermission.add_associated_investmentproject.value,
                'Can add evidence group for associated investment projects'
            ),
            (
                EvidenceGroupPermission.change_associated_investmentproject.value,
                'Can change evidence group for associated investment projects'
            ),
        )
        default_permissions = (
            'add_all',
            'change_all',
            'delete',
        )

    def __str__(self):
        """Human readable representation of the object."""
        return f'{self.investment_project.name} - {self.name}'


class EvidenceDocument(AbstractEntityDocumentModel):
    """Evidence Document model."""

    BUCKET = 'investment'

    evidence_group = models.ForeignKey(
        EvidenceGroup,
        related_name='documents',
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = 'investment project evidence document'

    def __str__(self):
        """Human readable representation of the object."""
        return f'{self.evidence.name} - {self.original_filename}'
