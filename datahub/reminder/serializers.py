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
    """Serializer for Upcoming Estimated Land Date Reminder."""

    project = NestedInvestmentProjectSerializer(many=False, read_only=True)

    class Meta:
        model = NoRecentInvestmentInteractionReminder
        fields = ('id', 'created_on', 'event', 'project')
