import collections

from rest_framework import serializers

from datahub.investment.project.models import InvestmentProject
from datahub.reminder.models import (
    NoRecentInvestmentInteractionReminder,
    NoRecentInvestmentInteractionSubscription,
    UpcomingEstimatedLandDateReminder,
    UpcomingEstimatedLandDateSubscription,
)


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


class NestedInvestmentProjectSerializer(serializers.ModelSerializer):
    """Simple Project serializer to nest inside reminders."""

    class Meta:
        model = InvestmentProject
        fields = ('id', 'name', 'project_code')


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
