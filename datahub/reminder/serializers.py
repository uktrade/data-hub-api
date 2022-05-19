from rest_framework import serializers

from datahub.reminder.models import (
    NoRecentInvestmentInteractionSubscription,
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
