import uuid

from django.conf import settings
from django.db import models


MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


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
