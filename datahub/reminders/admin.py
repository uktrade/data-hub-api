from django.contrib import admin

from datahub.reminders.models import (
    NoRecentInteractionSubscription,
    UpcomingEstimatedLandDateSubscription,
)


@admin.register(NoRecentInteractionSubscription)
class NoRecentInteractionSubscriptionAdmin(admin.ModelAdmin):
    """No Recent Interaction Subscription admin."""


@admin.register(UpcomingEstimatedLandDateSubscription)
class UpcomingEstimatedLandDateSubscriptionAdmin(admin.ModelAdmin):
    """Upcoming Estimated Land Date Subscription admin."""
