from uuid import uuid4

from django.conf import settings
from django.db import models

from datahub.core.models import BaseModel


class CompanyReferral(BaseModel):
    """
    An internal referral of a company, from one adviser (the creator of the referrer)
    to another (the recipient).
    """

    class Status(models.TextChoices):
        OUTSTANDING = ('outstanding', 'Outstanding')
        CLOSED = ('closed', 'Closed')
        COMPLETE = ('complete', 'Complete')

    class ClosureReason(models.TextChoices):
        UNREACHABLE = (
            'unreachable',
            'The company or contact couldn’t be reached',
        )
        INSUFFICIENT_INFORMATION = (
            'insufficient_information',
            'The information in this referral is insufficient',
        )
        WRONG_RECIPIENT = (
            'wrong_recipient',
            'I’m not the right person for this referral',
        )

    id = models.UUIDField(primary_key=True, default=uuid4)
    closure_reason = models.CharField(
        blank=True,
        max_length=settings.CHAR_FIELD_MAX_LENGTH,
        choices=ClosureReason.choices,
    )
    closed_by = models.ForeignKey(
        'company.Advisor',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='closed_referrals',
    )
    closed_on = models.DateTimeField(null=True, blank=True)
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
    interaction = models.OneToOneField(
        'interaction.Interaction',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
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
