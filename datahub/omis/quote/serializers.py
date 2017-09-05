from rest_framework import serializers

from datahub.company.serializers import NestedAdviserField

from .models import Quote


class ExpandParamSerializer(serializers.Serializer):
    """Holds the `expand` param for getting the complete details of an object."""

    expand = serializers.BooleanField(default=False)


class BasicQuoteSerializer(serializers.ModelSerializer):
    """
    Basic Quote DRF serializer.

    It does not include the content of a quote which is usually long.
    """

    created_on = serializers.DateTimeField(read_only=True)
    created_by = NestedAdviserField(read_only=True)
    cancelled_on = serializers.DateTimeField(read_only=True)
    cancelled_by = NestedAdviserField(read_only=True)

    def preview(self):
        """Same as create but without saving the changes."""
        self.instance = self.create(self.validated_data, commit=False)
        return self.instance

    def cancel(self):
        """Call `order.reopen` to cancel this quote."""
        order = self.context['order']
        current_user = self.context['current_user']

        order.reopen(by=current_user)
        self.instance = order.quote
        return self.instance

    def create(self, validated_data, commit=True):
        """Call `order.generate_quote` instead of creating the object directly."""
        order = self.context['order']

        order.generate_quote(validated_data, commit=commit)
        return order.quote

    class Meta:  # noqa: D101
        model = Quote
        fields = [
            'created_on',
            'created_by',
            'cancelled_on',
            'cancelled_by',
        ]


class ExpandedQuoteSerializer(BasicQuoteSerializer):
    """
    Expanded Quote DRF serializer.

    It includes the content of a quote which is usually long.
    """

    content = serializers.CharField(read_only=True)

    class Meta(BasicQuoteSerializer.Meta):  # noqa: D101
        fields = BasicQuoteSerializer.Meta.fields + [
            'content',
        ]
