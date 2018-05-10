"""Investment project proposition models."""

import uuid

from django.conf import settings
from django.db import models
from django.utils.timezone import now

from datahub.core.exceptions import APIConflictException
from datahub.core.models import BaseModel
from datahub.investment.proposition.constants import PropositionStatus

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class Proposition(BaseModel):
    """Proposition model."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    investment_project = models.ForeignKey(
        'investment.InvestmentProject', on_delete=models.CASCADE, related_name='proposition'
    )
    adviser = models.ForeignKey(
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
        self.modified_on = now()
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
