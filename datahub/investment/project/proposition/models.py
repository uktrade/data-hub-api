"""Investment project proposition models."""

import uuid

from django.conf import settings
from django.db import models
from rest_framework.exceptions import ValidationError
from rest_framework.reverse import reverse

from datahub.core.exceptions import APIConflictException
from datahub.core.models import BaseModel
from datahub.core.utils import StrEnum
from datahub.documents.models import AbstractEntityDocumentModel, UploadStatus
from datahub.investment.project.proposition.constants import PropositionStatus

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class PropositionPermission(StrEnum):
    """
    Permission codename constants.

    (Defined here rather than in permissions to avoid an import of that module.)


    The following codenames mean that the user can view, change, add any type of
    proposition:

    view_all_proposition
    change_all_proposition
    add_all_proposition
    delete_all_proposition

    (user is not allowed to delete a proposition, it can only be abandoned)

    The following codenames mean that the user can only view, change and add propositions for
    investment projects that they are associated with:

    view_associated_proposition
    change_associated_proposition
    add_associated_proposition

    An associated project has the same meaning that it does in investment projects (that is a
    project that was created by an adviser in the same team, or an adviser in the same team has
    been linked to the project).

    Note that permissions on other models are independent of permissions on propositions. Also
    note that if both *_all_* and *_associated__* permissions are assigned to the
    same user,  the *_all_* permission will be the effective one.
    """

    view_all = 'view_all_proposition'
    view_associated = 'view_associated_proposition'
    change_all = 'change_all_proposition'
    change_associated = 'change_associated_proposition'
    add_all = 'add_all_proposition'
    add_associated = 'add_associated_proposition'
    delete_all = 'delete_all_proposition'


class PropositionDocumentPermission(StrEnum):
    """
    Permission codename constants.

    (Defined here rather than in permissions to avoid an import of that module.)


    The following codenames mean that the user can view, change, add or delete any type of
    proposition document:

    view_all_propositiondocument
    change_all_propositiondocument
    add_all_propositiondocument
    delete_all_propositiondocument


    The following codenames mean that the user can only view, change and add proposition
    documents for investment projects that they are associated with:

    view_associated__propositiondocument
    change_associated_propositiondocument
    add_associated_propositiondocument
    delete_associated_propositiondocument

    An associated project has the same meaning that it does in investment projects (that is a
    project that was created by an adviser in the same team, or an adviser in the same team has
    been linked to the project).

    Note that permissions on other models are independent of permissions on proposition documents.
    Also note that if both *_all_* and *_associated_* permissions are
    assigned to the same user,  the *_all_* permission will be the effective one.
    """

    view_all = 'view_all_propositiondocument'
    view_associated = 'view_associated_propositiondocument'
    change_all = 'change_all_propositiondocument'
    change_associated = 'change_associated_propositiondocument'
    add_all = 'add_all_propositiondocument'
    add_associated = 'add_associated_propositiondocument'
    delete_all = 'delete_all_propositiondocument'
    delete_associated = 'delete_associated_propositiondocument'


class Proposition(BaseModel):
    """Proposition model."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    investment_project = models.ForeignKey(
        'investment.InvestmentProject', on_delete=models.CASCADE, related_name='proposition',
    )
    # adviser to whom a proposition is assigned
    adviser = models.ForeignKey(
        'company.Advisor', on_delete=models.CASCADE, related_name='+',
    )
    deadline = models.DateField()
    status = models.CharField(
        max_length=MAX_LENGTH,
        choices=PropositionStatus.choices,
        default=PropositionStatus.ONGOING,
    )

    name = models.CharField(max_length=MAX_LENGTH)
    scope = models.TextField()

    details = models.TextField(blank=True)

    def __str__(self):
        """Human readable representation of the object."""
        return f'{self.investment_project.name} - {self.name}'

    def _change_status(self, status, by, details):
        """Change status of a proposition."""
        if self.status != PropositionStatus.ONGOING:
            raise APIConflictException(
                f'The action cannot be performed in the current status {self.status}.',
            )
        self.status = status
        self.modified_by = by
        self.details = details
        self.save()

    def complete(self, by, details):
        """
        Complete a proposition

        :param by: the adviser who marked the proposition as complete
        :param details: details of completion
        :raises ValidationError: when trying to complete proposition without uploaded documents
        :raises APIConflictException: when proposition status is not ongoing
        """
        if self.documents.filter(document__status=UploadStatus.VIRUS_SCANNED).count() == 0:
            raise ValidationError({
                'non_field_errors': ['Proposition has no documents uploaded.'],
            })
        self._change_status(PropositionStatus.COMPLETED, by, details)

    def abandon(self, by, details):
        """
        Abandon a proposition

        :param by: the adviser who marked the proposition as abandoned
        :param details: reason of abandonment
        """
        self._change_status(PropositionStatus.ABANDONED, by, details)

    class Meta:
        permissions = (
            (
                PropositionPermission.view_associated.value,
                'Can view proposition for associated investment projects',
            ),
            (
                PropositionPermission.add_associated.value,
                'Can add proposition for associated investment projects',
            ),
            (
                PropositionPermission.change_associated.value,
                'Can change proposition for associated investment projects',
            ),
        )
        default_permissions = (
            'add_all',
            'change_all',
            'delete_all',
            'view_all',
        )


class PropositionDocument(AbstractEntityDocumentModel):
    """Investment Project Proposition Document."""

    BUCKET = 'investment'

    proposition = models.ForeignKey(
        Proposition,
        related_name='documents',
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = 'investment project proposition document'
        permissions = (
            (
                PropositionDocumentPermission.add_associated.value,
                'Can add proposition document for associated investment projects',
            ),
            (
                PropositionDocumentPermission.change_associated.value,
                'Can change proposition document for associated investment projects',
            ),
            (
                PropositionDocumentPermission.delete_associated.value,
                'Can delete proposition document for associated investment projects',
            ),
            (
                PropositionDocumentPermission.view_associated.value,
                'Can view proposition document for associated investment projects',
            ),
        )
        default_permissions = (
            'add_all',
            'change_all',
            'delete_all',
            'view_all',
        )

    @property
    def url(self):
        """Returns URL to download endpoint."""
        return reverse(
            'api-v3:investment:proposition:document-item-download',
            kwargs={
                'proposition_pk': self.proposition.pk,
                'project_pk': self.proposition.investment_project.pk,
                'entity_document_pk': self.pk,
            },
        )
