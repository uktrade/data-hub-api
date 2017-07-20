from rest_framework import serializers

from datahub.company.models import Advisor, Company, Contact
from datahub.core.serializers import NestedRelatedField
from datahub.metadata.models import Country, Team

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


def existing_adviser(adviser_id):
    """
    DRF Validator. It raises a ValidationError if adviser_id is not a valid adviser id.
    """
    try:
        Advisor.objects.get(id=adviser_id)
    except Advisor.DoesNotExist:
        raise serializers.ValidationError(f'{adviser_id} is not a valid adviser')
    return adviser_id


class SubscribedAdviserSerializer(serializers.Serializer):
    """
    DRF serializer for an adviser subscribed to an order.
    """

    id = serializers.UUIDField(validators=[existing_adviser])
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    dit_team = NestedRelatedField(Team, read_only=True)
