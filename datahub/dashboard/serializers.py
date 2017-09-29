from rest_framework import serializers

from datahub.company.serializers import NestedContactSerializer
from datahub.interaction.serializers import InteractionSerializerReadV1


class IntelligentHomepageSerializer(serializers.Serializer):
    """Intelligent homepage serializer."""

    interactions = InteractionSerializerReadV1(many=True)
    contacts = NestedContactSerializer(many=True)

    class Meta:  # noqa: D101
        fields = '__all__'


class LimitParamSerializer(serializers.Serializer):
    """Serialiser for limit param in the home page endpoint query string."""

    limit = serializers.IntegerField(min_value=1, default=5)
