"""Investment project proposition models."""

import uuid

from django.conf import settings
from django.db import models
from django.utils.timezone import now

from datahub.core.models import BaseModel
from datahub.investment.proposition.constants import PropositionStatus
from datahub.investment.proposition.exceptions import Conflict

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
    deadline = models.DateField(blank=True, null=True)
    status = models.CharField(
        max_length=MAX_LENGTH, choices=PropositionStatus, default=PropositionStatus.ongoing
    )

    name = models.CharField(max_length=MAX_LENGTH)
    scope = models.TextField(blank=True)

    reason_abandoned = models.TextField(blank=True)
    abandoned_on = models.DateTimeField(blank=True, null=True)

    completed_details = models.TextField(blank=True)
    completed_on = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        """Human readable representation of the object."""
        return self.name

    def complete(self, by, details):
        """
        Complete a proposition

        :param by: the adviser who marked the proposition as complete
        :param details: details of completion
        """
        if self.status != PropositionStatus.ongoing:
            raise Conflict(
                f'The action cannot be performed in the current status {self.status}.'
            )
        self.status = PropositionStatus.completed
        self.modified_by = by
        self.completed_on = now()
        self.completed_details = details
        self.save()

    def abandon(self, by, reason):
        """
        Abandon a proposition

        :param by: the adviser who marked the proposition as abandoned
        :param reason: reason of abandonment
        """
        if self.status != PropositionStatus.ongoing:
            raise Conflict(
                f'The action cannot be performed in the current status {self.status}.'
            )
        self.status = PropositionStatus.abandoned
        self.modified_by = by
        self.abandoned_on = now()
        self.reason_abandoned = reason
        self.save()
