from rest_framework import serializers

from datahub.company.models import Contact
from datahub.company.serializers import NestedAdviserField
from datahub.core.serializers import NestedRelatedField
from .models import Quote


class QuoteSerializer(serializers.ModelSerializer):
    """Quote DRF serializer."""

    created_by = NestedAdviserField(read_only=True)
    cancelled_by = NestedAdviserField(read_only=True)
    accepted_by = NestedRelatedField(Contact, read_only=True)
    terms_and_conditions = serializers.CharField(
        source='terms_and_conditions.content', default=''
    )

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
        current_user = self.context['current_user']

        order.generate_quote(by=current_user, commit=commit)
        return order.quote

    class Meta:
        model = Quote
        fields = [
            'created_on',
            'created_by',
            'cancelled_on',
            'cancelled_by',
            'accepted_on',
            'accepted_by',
            'expires_on',
            'content',
            'terms_and_conditions',
        ]
        read_only_fields = fields


class PublicQuoteSerializer(serializers.ModelSerializer):
    """Public Quote DRF serializer."""

    terms_and_conditions = serializers.CharField(
        source='terms_and_conditions.content', default=''
    )

    def accept(self):
        """Call `order.accept_quote` to accept this quote."""
        order = self.context['order']

        order.accept_quote(by=order.contact)  # assume that the contact accepted the quote
        self.instance = order.quote
        return self.instance

    class Meta:
        model = Quote
        fields = [
            'created_on',
            'cancelled_on',
            'accepted_on',
            'expires_on',
            'content',
            'terms_and_conditions',
        ]
        read_only_fields = fields
