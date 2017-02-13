from rest_framework import serializers
from rest_framework_json_api import serializers as json_api_serializers
from rest_framework_json_api.relations import ResourceRelatedField

from datahub.company.models import Advisor, Company, Contact
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

    company = ResourceRelatedField(
        queryset=Company.objects,
        related_link_view_name='v1:company-detail',
        related_link_url_kwarg='pk',
    )
    contact = ResourceRelatedField(
        queryset=Contact.objects,
        related_link_view_name='v1:contact-detail',
        related_link_url_kwarg='pk',
    )
    dit_advisor = ResourceRelatedField(
        queryset=Advisor.objects,
        related_link_view_name='v1:advisor-detail',
        related_link_url_kwarg='pk',
    )

    class Meta:  # noqa: D101
        model = ServiceDelivery
        exclude = ('service_offer', )
