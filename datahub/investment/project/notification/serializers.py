from rest_framework import serializers

from datahub.investment.project.notification.models import InvestmentNotificationSubscription


class ListMultipleChoiceField(serializers.MultipleChoiceField):
    """
    A MultipleChoiceField, but returns a `list` instead of `set`.
    """

    def to_internal_value(self, data):
        """Converts set to list."""
        return list(super().to_internal_value(data))


class InvestmentNotificationSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for Investment Project Notification Subscription."""

    estimated_land_date = ListMultipleChoiceField(
        choices=InvestmentNotificationSubscription.EstimatedLandDateNotification.choices,
    )

    class Meta:
        model = InvestmentNotificationSubscription
        fields = (
            'estimated_land_date',
        )
