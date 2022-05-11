import uuid

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models


class BaseSubscription(models.Model):
    """
    Base model for reminder subscriptions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    adviser = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='+',
    )
    notification_days = ArrayField(models.PositiveSmallIntegerField(), size=5)

    class Meta:
        abstract = True


class NoRecentInteractionSubscription(BaseSubscription):
    """
    Subscription to get reminders about projects with no recent interactions.
    """


class UpcomingEstimatedLandDateSubscription(BaseSubscription):
    """
    Subscription to get reminders about upcoming estimated land dates.
    """
