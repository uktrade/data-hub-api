from rest_framework import serializers

from datahub.omis.payment.constants import PaymentMethod
from datahub.omis.payment.models import Payment, PaymentGatewaySession


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
        default=PaymentMethod.BACS,
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


class PaymentGatewaySessionSerializer(serializers.ModelSerializer):
    """Payment Gateway Session DRF serializer."""

    payment_url = serializers.CharField(source='get_payment_url', required=False)

    class Meta:
        model = PaymentGatewaySession
        fields = (
            'id',
            'created_on',
            'status',
            'payment_url',
        )
        read_only_fields = fields

    def create(self, validated_data):
        """Create a payment gateway session."""
        return PaymentGatewaySession.objects.create_from_order(
            self.context['order'],
            validated_data,
        )
