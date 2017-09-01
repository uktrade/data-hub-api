from rest_framework import serializers

from datahub.company.serializers import NestedAdviserField

from .models import Quote


class QuoteSerializer(serializers.ModelSerializer):
    """Quote DRF serializer."""

    created_on = serializers.DateTimeField(read_only=True)
    created_by = NestedAdviserField(read_only=True)

    def create(self, validated_data):
        """Call `order.generate_quote` instead of creating the object directly."""
        order = self.context['order']
        order.generate_quote(validated_data)

        return order.quote

    class Meta:  # noqa: D101
        model = Quote
        fields = [
            'created_on',
            'created_by',
        ]
