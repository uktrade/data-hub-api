import uuid

from django.conf import settings
from django.db import models

from datahub.core.fields import MultipleChoiceField

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


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


class NotificationInnerTemplate(models.Model):
    """Notification inner template content."""

    class NotificationType(models.TextChoices):
        NOT_SET = ('not_set', 'Not set')
        NO_RECENT_INTERACTION = (
            'no_investment_recent_interaction',
            'No investment recent interaction',
        )
        UPCOMING_ESTIMATED_LAND_DATE = (
            'upcoming_estimated_land_date',
            'Upcoming estimated land date',
        )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    content = models.TextField()
    notification_type = models.CharField(
        max_length=MAX_LENGTH,
        choices=NotificationType.choices,
        default=NotificationType.NOT_SET,
        unique=True,
    )
    created_on = models.DateTimeField(auto_now_add=True)
