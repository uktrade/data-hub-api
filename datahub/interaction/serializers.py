from rest_framework import serializers
from rest_framework_json_api import serializers as json_api_serializers

from datahub.company.serializers import AdvisorSerializer
from .models import Interaction, ServiceDelivery


class InteractionSerializerRead(serializers.ModelSerializer):
    """Interaction Serializer."""

    dit_advisor = AdvisorSerializer()

    class Meta:  # noqa: D101
        model = Interaction
        depth = 2
        fields = '__all__'


class InteractionSerializerWrite(serializers.ModelSerializer):
    """Interaction Serializer for writing operations."""

    class Meta:  # noqa: D101
        model = Interaction
        fields = '__all__'


class ServiceDeliverySerializerV2(json_api_serializers.ModelSerializer):
    """Service Delivery serializer."""

    class Meta:  # noqa: D101
        model = ServiceDelivery
        fields = (
            'id',
            'date',
            'company',
            'contact',
            'service',
            'subject',
            'dit_advisor',
            'event',
            'notes',
            'dit_team',
            'status',
            'uk_region',
            'sector',
            'country_of_interest',
            'feedback',
            'url', )
