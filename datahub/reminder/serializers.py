import collections

from rest_framework import serializers

from datahub.company.models import Company
from datahub.company.serializers import NestedAdviserWithTeamField
from datahub.interaction.models import Interaction
from datahub.interaction.serializers import BaseInteractionSerializer
from datahub.investment.project.models import InvestmentProject
from datahub.reminder.models import (
    NewExportInteractionReminder,
    NewExportInteractionSubscription,
    NoRecentExportInteractionReminder,
    NoRecentExportInteractionSubscription,
    NoRecentInvestmentInteractionReminder,
    NoRecentInvestmentInteractionSubscription,
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
from datahub.task.models import Task
from datahub.task.serializers import TaskSerializer


class NoRecentExportInteractionSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for No Recent Export Interaction Subscription."""

    def validate_reminder_days(self, reminder_days):
        duplicate_days = [
            day for day, count in collections.Counter(reminder_days).items() if count > 1
        ]
        if len(duplicate_days) > 0:
            raise serializers.ValidationError(
                f'Duplicate reminder days are not allowed {duplicate_days}',
            )
        return reminder_days

    class Meta:
        model = NoRecentExportInteractionSubscription
        fields = ('reminder_days', 'email_reminders_enabled')


class NewExportInteractionSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for New Export Interaction Subscription."""

    def validate_reminder_days(self, reminder_days):
        duplicate_days = [
            day for day, count in collections.Counter(reminder_days).items() if count > 1
        ]
        if len(duplicate_days) > 0:
            raise serializers.ValidationError(
                f'Duplicate reminder days are not allowed {duplicate_days}',
            )
        return reminder_days

    class Meta:
        model = NewExportInteractionSubscription
        fields = ('reminder_days', 'email_reminders_enabled')


class NoRecentInvestmentInteractionSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for No Recent Investment Interaction Subscription."""

    def validate_reminder_days(self, reminder_days):
        duplicate_days = [
            day for day, count in collections.Counter(reminder_days).items() if count > 1
        ]
        if len(duplicate_days) > 0:
            raise serializers.ValidationError(
                f'Duplicate reminder days are not allowed {duplicate_days}',
            )
        return reminder_days

    class Meta:
        model = NoRecentInvestmentInteractionSubscription
        fields = ('reminder_days', 'email_reminders_enabled')


class UpcomingEstimatedLandDateSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for Upcoming Estimated Land Date Subscription."""

    class Meta:
        model = UpcomingEstimatedLandDateSubscription
        fields = ('reminder_days', 'email_reminders_enabled')


class UpcomingTaskReminderSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for Upcoming Task Subscription."""

    class Meta:
        model = UpcomingTaskReminderSubscription
        fields = ('reminder_days', 'email_reminders_enabled')


class TaskAssignedToMeFromOthersSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for Upcoming Task Subscription."""

    class Meta:
        model = TaskAssignedToMeFromOthersSubscription
        fields = ('email_reminders_enabled',)


class TaskOverdueSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for Task Overdue Subscription."""

    class Meta:
        model = TaskOverdueSubscription
        fields = ('reminder_days', 'email_reminders_enabled')


class TaskAmendedByOthersSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for Upcoming Task Subscription."""

    class Meta:
        model = TaskAmendedByOthersSubscription
        fields = ('email_reminders_enabled',)


class TaskCompletedSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for Task Completed Subscription."""

    class Meta:
        model = TaskCompletedSubscription
        fields = ('email_reminders_enabled',)


class TaskDeletedByOthersSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for Task Deleted By Others Subscription."""

    class Meta:
        model = TaskDeletedByOthersSubscription
        fields = ('email_reminders_enabled',)


class NestedInvestmentProjectSerializer(serializers.ModelSerializer):
    """Simple Project serializer to nest inside reminders."""

    class Meta:
        model = InvestmentProject
        fields = ('id', 'name', 'project_code')


class NestedInteractionSerializer(BaseInteractionSerializer):
    """Selects relevant fields from Interaction serializer to nest inside reminders."""

    created_by = NestedAdviserWithTeamField(read_only=True)

    class Meta:
        model = Interaction
        fields = ('created_by', 'kind', 'subject', 'date')


class NestedExportCompanySerializer(serializers.ModelSerializer):
    """Simple Company serializer to nest inside reminders."""

    class Meta:
        model = Company
        fields = ('id', 'name')


class UpcomingEstimatedLandDateReminderSerializer(serializers.ModelSerializer):
    """Serializer for Upcoming Estimated Land Date Reminder."""

    project = NestedInvestmentProjectSerializer(many=False, read_only=True)

    class Meta:
        model = UpcomingEstimatedLandDateReminder
        fields = ('id', 'created_on', 'event', 'project')


class NoRecentInvestmentInteractionReminderSerializer(serializers.ModelSerializer):
    """Serializer for No Recent Investment Interaction Reminder."""

    project = NestedInvestmentProjectSerializer(many=False, read_only=True)

    class Meta:
        model = NoRecentInvestmentInteractionReminder
        fields = ('id', 'created_on', 'event', 'project')


class NewExportInteractionReminderSerializer(serializers.ModelSerializer):
    """Serializer for New Export Interaction Reminder."""

    company = NestedExportCompanySerializer(many=False, read_only=True)
    interaction = NestedInteractionSerializer(many=False, read_only=True)

    class Meta:
        model = NewExportInteractionReminder
        fields = ('id', 'created_on', 'last_interaction_date', 'event', 'company', 'interaction')


class NoRecentExportInteractionReminderSerializer(serializers.ModelSerializer):
    """Serializer for No Recent Export Interaction Reminder."""

    company = NestedExportCompanySerializer(many=False, read_only=True)
    interaction = NestedInteractionSerializer(many=False, read_only=True)

    class Meta:
        model = NoRecentExportInteractionReminder
        fields = ('id', 'created_on', 'last_interaction_date', 'event', 'company', 'interaction')


class ReminderTaskSerializer(TaskSerializer):
    """Serializer for the task in a reminder."""

    class Meta:
        model = Task
        fields = (
            'id',
            'title',
            'investment_project',
            'company',
            'due_date',
            'interaction',
        )


class UpcomingTaskReminderSerializer(serializers.ModelSerializer):
    """Serializer for Upcoming Investment Project Task Reminder."""

    task = ReminderTaskSerializer()

    class Meta:
        model = UpcomingTaskReminder
        fields = (
            'id',
            'event',
            'created_on',
            'task',
        )


class TaskAssignedToMeFromOthersReminderSerializer(serializers.ModelSerializer):
    """Serializer for task assigned to me from others."""

    task = ReminderTaskSerializer()

    class Meta:
        model = TaskAssignedToMeFromOthersReminder
        fields = (
            'id',
            'event',
            'created_on',
            'task',
        )


class TaskOverdueReminderSerializer(serializers.ModelSerializer):
    """Serializer for task overdue."""

    task = ReminderTaskSerializer()

    class Meta:
        model = TaskOverdueReminder
        fields = (
            'id',
            'event',
            'created_on',
            'task',
        )


class TaskCompletedReminderSerializer(serializers.ModelSerializer):
    """Serializer for task completed."""

    task = ReminderTaskSerializer()

    class Meta:
        model = TaskCompletedReminder
        fields = (
            'id',
            'event',
            'created_on',
            'task',
        )


class TaskAmendedByOthersReminderSerializer(serializers.ModelSerializer):
    """Serializer for task completed."""

    task = ReminderTaskSerializer()

    class Meta:
        model = TaskCompletedReminder
        fields = (
            'id',
            'event',
            'created_on',
            'task',
        )


class TaskDeletedByOthersReminderSerializer(serializers.ModelSerializer):
    """Serializer for task completed."""

    task = ReminderTaskSerializer()

    class Meta:
        model = TaskDeletedByOthersReminder
        fields = (
            'id',
            'event',
            'created_on',
            'task',
        )
