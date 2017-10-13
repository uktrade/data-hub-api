from rest_framework import serializers

from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    """Payment DRF serializer."""

    class Meta:
        model = Payment
        fields = (
            'created_on',
            'reference',
            'transaction_reference',
            'additional_reference',
            'amount',
            'method',
            'received_on',
        )
        read_only_fields = (
            'created_on',
            'reference',
            'additional_reference',
            'method',
        )
