from rest_framework import serializers

from datahub.company.serializers import AdvisorSerializer
from .models import Interaction


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
