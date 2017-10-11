from rest_framework import serializers

from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    """Payment DRF serializer."""

    class Meta:  # noqa: D101
        model = Payment
        fields = (
            'created_on',
            'reference',
            'transaction_reference',
            'additional_reference',
            'amount',
            'method',
            'payment_received_on',
        )
        read_only_fields = (
            'created_on',
            'reference',
            'additional_reference',
            'method',
        )
