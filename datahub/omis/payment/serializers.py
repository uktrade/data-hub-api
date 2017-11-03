from rest_framework import serializers

from .constants import PaymentMethod
from .models import Payment


class PaymentListSerializer(serializers.ListSerializer):
    """DRF List Serializer for Payment objects."""

    def create(self, validated_data):
        """Create payments."""
        order = self.context['order']
        created_by = self.context['current_user']

        order.mark_as_paid(created_by, validated_data)
        return list(order.payments.all())


class PaymentSerializer(serializers.ModelSerializer):
    """Payment DRF serializer."""

    method = serializers.ChoiceField(
        choices=[
            method
            for method in PaymentMethod
            if method[0] in ('bacs', 'manual')
        ],
        default=PaymentMethod.bacs
    )

    class Meta:
        model = Payment
        list_serializer_class = PaymentListSerializer
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
        )
