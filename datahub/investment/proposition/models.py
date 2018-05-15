"""Investment project proposition models."""

import uuid

from django.conf import settings
from django.db import models
from django.utils.timezone import now

from datahub.core.exceptions import APIConflictException
from datahub.core.models import BaseModel
from datahub.core.utils import StrEnum
from datahub.investment.proposition.constants import PropositionStatus

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class PropositionPermission(StrEnum):
    """
    Permission codename constants.

    (Defined here rather than in permissions to avoid an import of that module.)


    The following codenames mean that the user can read, change, add or delete any type of
    proposition:

    read_all_proposition
    change_all_proposition
    add_all_proposition
    delete_proposition


    The following codenames mean that the user can only read, change and add propositions for
    investment projects that they are associated with:

    read_associated_investmentproject_proposition
    change_associated_investmentproject_proposition
    add_associated_investmentproject_proposition

    An associated project has the same meaning that it does in investment projects (that is a
    project that was created by an adviser in the same team, or an adviser in the same team has
    been linked to the project).

    Note that permissions on other models are independent of permissions on propositions. Also
    note that if both *_all_* and *_associated_investmentproject_* permissions are assigned to the
    same user,  the *_all_* permission will be the effective one.
    """

    read_all = 'read_all_proposition'
    read_associated_investmentproject = 'read_associated_investmentproject_proposition'
    change_all = 'change_all_proposition'
    change_associated_investmentproject = 'change_associated_investmentproject_proposition'
    add_all = 'add_all_proposition'
    add_associated_investmentproject = 'add_associated_investmentproject_proposition'
    delete = 'delete_proposition'


class Proposition(BaseModel):
    """Proposition model."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    investment_project = models.ForeignKey(
        'investment.InvestmentProject', on_delete=models.CASCADE, related_name='proposition'
    )
    assigned_to = models.ForeignKey(
        'company.Advisor', on_delete=models.CASCADE, related_name='+'
    )
    deadline = models.DateField()
    status = models.CharField(
        max_length=MAX_LENGTH, choices=PropositionStatus, default=PropositionStatus.ongoing
    )

    name = models.CharField(max_length=MAX_LENGTH)
    scope = models.TextField()

    details = models.TextField()

    def __str__(self):
        """Human readable representation of the object."""
        return self.name

    def _change_status(self, status, by, details):
        """Change status of a proposition."""
        if self.status != PropositionStatus.ongoing:
            raise APIConflictException(
                f'The action cannot be performed in the current status {self.status}.'
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
        """
        self._change_status(PropositionStatus.completed, by, details)

    def abandon(self, by, details):
        """
        Abandon a proposition

        :param by: the adviser who marked the proposition as abandoned
        :param details: reason of abandonment
        """
        self._change_status(PropositionStatus.abandoned, by, details)

    class Meta:
        permissions = (
            (
                PropositionPermission.read_all.value,
                'Can read all proposition'
            ),
            (
                PropositionPermission.read_associated_investmentproject.value,
                'Can read proposition for associated investment projects'
            ),
            (
                PropositionPermission.add_associated_investmentproject.value,
                'Can add proposition for associated investment projects'
            ),
            (
                PropositionPermission.change_associated_investmentproject.value,
                'Can change proposition for associated investment projects'
            ),
        )
        default_permissions = (
            'add_all',
            'change_all',
            'delete',
        )
