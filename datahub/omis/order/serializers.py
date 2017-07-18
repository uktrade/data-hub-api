from rest_framework import serializers

from datahub.company.models import Company, Contact
from datahub.core.serializers import NestedRelatedField
from datahub.metadata.models import Country

from .models import Order


class OrderSerializer(serializers.ModelSerializer):
    """Order DRF serializer"""

    id = serializers.UUIDField(read_only=True)
    reference = serializers.CharField(read_only=True)
    company = NestedRelatedField(Company)
    contact = NestedRelatedField(Contact)
    primary_market = NestedRelatedField(Country)

    class Meta:  # noqa: D101
        model = Order
        fields = [
            'id',
            'reference',
            'company',
            'contact',
            'primary_market'
        ]

    def validate(self, data):
        """
        Extra check that a contact works at the given company.
        """
        if data['contact'].company != data['company']:
            raise serializers.ValidationError({
                'contact': 'The contact does not work at the given company.'
            })

        return data
