from uuid import uuid4

from django.conf import settings
from django.db import models

from datahub.core.models import BaseModel


class CompanyReferral(BaseModel):
    """
    An internal referral of a company, from one adviser (the creator of the referrer)
    to another (the recipient).

    TODO:
    - add additional statuses
    - add a OneToOneField between this model and Interaction (could go on either model)
    """

    class Status(models.TextChoices):
        OUTSTANDING = ('outstanding', 'Outstanding')

    id = models.UUIDField(primary_key=True, default=uuid4)
    company = models.ForeignKey(
        'company.Company',
        on_delete=models.CASCADE,
        related_name='referrals',
    )
    contact = models.ForeignKey(
        'company.Contact',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='referrals',
    )
    recipient = models.ForeignKey(
        'company.Advisor',
        on_delete=models.CASCADE,
        related_name='received_referrals',
    )
    status = models.CharField(
        max_length=settings.CHAR_FIELD_MAX_LENGTH,
        choices=Status.choices,
        default=Status.OUTSTANDING,
    )
    completed_by = models.ForeignKey(
        'company.Advisor',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='completed_referrals',
    )
    completed_on = models.DateTimeField(null=True, blank=True)
    subject = models.CharField(max_length=settings.CHAR_FIELD_MAX_LENGTH)
    notes = models.TextField(blank=True)

    def __str__(self):
        """Human-friendly representation (for admin etc.)."""
        return f'{self.company} – {self.subject}'
