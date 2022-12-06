from django.contrib import admin

from datahub.reminder.models import (
    NewExportInteractionSubscription,
    NoRecentExportInteractionReminder,
    NoRecentExportInteractionSubscription,
    NoRecentInvestmentInteractionReminder,
    NoRecentInvestmentInteractionSubscription,
    UpcomingEstimatedLandDateReminder,
    UpcomingEstimatedLandDateSubscription,
)


@admin.register(NoRecentExportInteractionSubscription)
class NoRecentExportInteractionSubscriptionAdmin(admin.ModelAdmin):
    """No Recent Export Interaction Subscription admin."""

    raw_id_fields = ('adviser',)


@admin.register(NewExportInteractionSubscription)
class NewExportInteractionSubscriptionAdmin(admin.ModelAdmin):
    """New Export Interaction Subscription admin."""

    raw_id_fields = ('adviser',)


@admin.register(NoRecentInvestmentInteractionSubscription)
class NoRecentInvestmentInteractionSubscriptionAdmin(admin.ModelAdmin):
    """No Recent Investment Interaction Subscription admin."""

    raw_id_fields = ('adviser',)


@admin.register(UpcomingEstimatedLandDateSubscription)
class UpcomingEstimatedLandDateSubscriptionAdmin(admin.ModelAdmin):
    """Upcoming Estimated Land Date Subscription admin."""

    raw_id_fields = ('adviser',)


@admin.register(NoRecentExportInteractionReminder)
class NoRecentExportInteractionReminderAdmin(admin.ModelAdmin):
    """No Recent Export Interaction Subscription admin."""

    raw_id_fields = ('adviser', 'company')


@admin.register(NoRecentInvestmentInteractionReminder)
class NoRecentInvestmentInteractionReminderAdmin(admin.ModelAdmin):
    """No Recent Investment Interaction Reminder admin."""

    raw_id_fields = ('adviser', 'project')


@admin.register(UpcomingEstimatedLandDateReminder)
class UpcomingEstimatedLandDateReminderAdmin(admin.ModelAdmin):
    """Upcoming Estimated Land Date Reminder admin."""

    raw_id_fields = ('adviser', 'project')
