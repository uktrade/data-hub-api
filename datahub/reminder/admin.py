from django.contrib import admin

from datahub.reminder.models import (
    NewExportInteractionReminder,
    NewExportInteractionSubscription,
    NoRecentExportInteractionReminder,
    NoRecentExportInteractionSubscription,
    NoRecentInvestmentInteractionReminder,
    NoRecentInvestmentInteractionSubscription,
    TaskAmendedByOthersReminder,
    TaskAmendedByOthersSubscription,
    TaskAssignedToMeFromOthersReminder,
    TaskAssignedToMeFromOthersSubscription,
    TaskCompletedReminder,
    TaskCompletedSubscription,
    TaskDeletedByOthersReminder,
    TaskDeletedByOthersSubscription,
    TaskOverdueReminder,
    TaskOverdueSubscription,
    UpcomingEstimatedLandDateReminder,
    UpcomingEstimatedLandDateSubscription,
    UpcomingTaskReminder,
    UpcomingTaskReminderSubscription,
)


@admin.register(NoRecentExportInteractionSubscription)
class NoRecentExportInteractionSubscriptionAdmin(admin.ModelAdmin):
    """No Recent Export Interaction Subscription admin."""

    raw_id_fields = ('adviser',)
    search_fields = (
        'pk',
        'adviser__pk',
    )


@admin.register(NewExportInteractionSubscription)
class NewExportInteractionSubscriptionAdmin(admin.ModelAdmin):
    """New Export Interaction Subscription admin."""

    raw_id_fields = ('adviser',)
    search_fields = (
        'pk',
        'adviser__pk',
    )


@admin.register(NoRecentInvestmentInteractionSubscription)
class NoRecentInvestmentInteractionSubscriptionAdmin(admin.ModelAdmin):
    """No Recent Investment Interaction Subscription admin."""

    raw_id_fields = ('adviser',)
    search_fields = (
        'pk',
        'adviser__pk',
    )


@admin.register(UpcomingEstimatedLandDateSubscription)
class UpcomingEstimatedLandDateSubscriptionAdmin(admin.ModelAdmin):
    """Upcoming Estimated Land Date Subscription admin."""

    raw_id_fields = ('adviser',)
    search_fields = (
        'pk',
        'adviser__pk',
    )


@admin.register(UpcomingTaskReminderSubscription)
class UpcomingTaskReminderSubscriptionAdmin(admin.ModelAdmin):
    """Upcoming Task Subscription admin."""

    raw_id_fields = ('adviser',)
    search_fields = (
        'pk',
        'adviser__pk',
    )


@admin.register(TaskAssignedToMeFromOthersSubscription)
class TaskAssignedToMeFromOthersSubscriptionAdmin(admin.ModelAdmin):
    """Task Assigned To Me From Others Subscription admin."""

    raw_id_fields = ('adviser',)
    search_fields = (
        'pk',
        'adviser__pk',
    )


@admin.register(TaskOverdueSubscription)
class TaskOverdueSubscriptionAdmin(admin.ModelAdmin):
    """Task Overdue Subscription admin."""

    raw_id_fields = ('adviser',)
    search_fields = (
        'pk',
        'adviser__pk',
    )


@admin.register(TaskAmendedByOthersSubscription)
class TaskAmendedByOthersSubscriptionAdmin(admin.ModelAdmin):
    """Task Amended By Others Subscription admin."""

    raw_id_fields = ('adviser',)
    search_fields = (
        'pk',
        'adviser__pk',
    )


@admin.register(TaskCompletedSubscription)
class TaskCompletedSubscriptionAdmin(admin.ModelAdmin):
    """Task Completed Subscription admin."""

    raw_id_fields = ('adviser',)
    search_fields = (
        'pk',
        'adviser__pk',
    )


@admin.register(NewExportInteractionReminder)
class NewExportInteractionReminderAdmin(admin.ModelAdmin):
    """New Export Interaction Reminder admin."""

    raw_id_fields = ('adviser', 'company', 'interaction')
    search_fields = (
        'pk',
        'adviser__pk',
        'company__pk',
        'interaction__pk',
    )


@admin.register(NoRecentExportInteractionReminder)
class NoRecentExportInteractionReminderAdmin(admin.ModelAdmin):
    """No Recent Export Interaction Reminder admin."""

    raw_id_fields = ('adviser', 'company', 'interaction')
    search_fields = (
        'pk',
        'adviser__pk',
        'company__pk',
        'interaction__pk',
    )


@admin.register(NoRecentInvestmentInteractionReminder)
class NoRecentInvestmentInteractionReminderAdmin(admin.ModelAdmin):
    """No Recent Investment Interaction Reminder admin."""

    raw_id_fields = ('adviser', 'project')
    search_fields = (
        'pk',
        'adviser__pk',
        'project__pk',
    )


@admin.register(UpcomingEstimatedLandDateReminder)
class UpcomingEstimatedLandDateReminderAdmin(admin.ModelAdmin):
    """Upcoming Estimated Land Date Reminder admin."""

    raw_id_fields = ('adviser', 'project')
    search_fields = (
        'pk',
        'adviser__pk',
        'project__pk',
    )


@admin.register(UpcomingTaskReminder)
class UpcomingTaskReminderAdmin(admin.ModelAdmin):
    """Upcoming task reminder admin."""

    raw_id_fields = ('adviser', 'task')
    list_display = (
        'id',
        'task',
        'event',
        'status',
        'adviser',
    )
    list_display_links = (
        'id',
        'adviser',
        'task',
    )
    search_fields = (
        'pk',
        'adviser__pk',
        'task__pk',
    )


@admin.register(TaskDeletedByOthersSubscription)
class TaskDeletedByOthersSubscriptionAdmin(admin.ModelAdmin):
    """Task Deleted By Others Subscription admin."""

    raw_id_fields = ('adviser',)
    search_fields = (
        'pk',
        'adviser__pk',
    )


@admin.register(TaskAssignedToMeFromOthersReminder)
class TaskAssignedToMeFromOthersReminderAdmin(admin.ModelAdmin):
    """Task assigned to me from others admin."""

    raw_id_fields = ('adviser', 'task')
    list_display = [
        'event',
        'adviser',
        'task',
    ]
    search_fields = (
        'pk',
        'adviser__pk',
        'task__pk',
    )


@admin.register(TaskAmendedByOthersReminder)
class TaskAmendedByOthersReminderAdmin(admin.ModelAdmin):
    """Task amended by others admin."""

    raw_id_fields = ('adviser', 'task')
    list_display = [
        'event',
        'adviser',
        'task',
    ]
    search_fields = (
        'pk',
        'adviser__pk',
        'task__pk',
    )


@admin.register(TaskOverdueReminder)
class TaskOverdueReminderAdmin(admin.ModelAdmin):
    """Task overdue admin."""

    raw_id_fields = ('adviser', 'task')
    list_display = [
        'event',
        'adviser',
        'task',
    ]
    search_fields = (
        'pk',
        'adviser__pk',
        'task__pk',
    )


@admin.register(TaskCompletedReminder)
class TaskCompletedReminderAdmin(admin.ModelAdmin):
    """Task completed admin."""

    raw_id_fields = ('adviser', 'task')
    list_display = [
        'event',
        'adviser',
        'task',
    ]
    search_fields = (
        'pk',
        'adviser__pk',
        'task__pk',
    )


@admin.register(TaskDeletedByOthersReminder)
class TaskDeletedByOthersReminderAdmin(admin.ModelAdmin):
    """Task deleted by others admin."""

    raw_id_fields = ('adviser', 'task')
    list_display = [
        'event',
        'adviser',
        'task',
    ]
    search_fields = (
        'pk',
        'adviser__pk',
        'task__pk',
    )
