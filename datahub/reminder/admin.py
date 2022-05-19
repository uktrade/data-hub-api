from django.contrib import admin

from datahub.reminder.models import (
    NoRecentInvestmentInteractionSubscription,
    UpcomingEstimatedLandDateSubscription,
)


@admin.register(NoRecentInvestmentInteractionSubscription)
class NoRecentInvestmentInteractionSubscriptionAdmin(admin.ModelAdmin):
    """No Recent Investment Interaction Subscription admin."""


@admin.register(UpcomingEstimatedLandDateSubscription)
class UpcomingEstimatedLandDateSubscriptionAdmin(admin.ModelAdmin):
    """Upcoming Estimated Land Date Subscription admin."""
