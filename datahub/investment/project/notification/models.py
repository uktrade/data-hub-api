from django.conf import settings
from django.db import models

from datahub.core.fields import MultipleChoiceField


class InvestmentNotificationSubscription(models.Model):
    """Notification subscription preferences."""

    class EstimatedLandDateNotification(models.TextChoices):
        ESTIMATED_LAND_DATE_30 = ('30', '30 days')
        ESTIMATED_LAND_DATE_60 = ('60', '60 days')

    id = models.BigAutoField(primary_key=True)
    adviser = models.ForeignKey(
        'company.Advisor', on_delete=models.CASCADE, related_name='+',
    )
    investment_project = models.ForeignKey(
        'investment.InvestmentProject', on_delete=models.CASCADE, related_name='notifications',
    )

    estimated_land_date = MultipleChoiceField(
        max_length=settings.CHAR_FIELD_MAX_LENGTH,
        choices=EstimatedLandDateNotification.choices,
        blank=True,
    )

    class Meta:
        default_permissions = ()
        constraints = [
            models.UniqueConstraint(
                fields=['investment_project_id', 'adviser_id'],
                name='Unique Investment Notification Subscription',
            ),
        ]

    def __str__(self):
        """Human-readable representation."""
        return f'{self.investment_project} – {self.adviser}'
