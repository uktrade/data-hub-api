from rest_framework import serializers

from datahub.company.serializers import AdviserSerializer, NestedContactSerializer
from datahub.interaction.models import Interaction


class InteractionSerializer(serializers.ModelSerializer):
    """Interaction serializer for IntelligentHomepageSerializer."""

    dit_adviser = AdviserSerializer()

    class Meta:  # noqa: D101
        model = Interaction
        depth = 2
        fields = '__all__'


class IntelligentHomepageSerializer(serializers.Serializer):
    """Intelligent homepage serializer."""

    interactions = InteractionSerializer(many=True)
    contacts = NestedContactSerializer(many=True)

    class Meta:  # noqa: D101
        fields = '__all__'


class LimitParamSerializer(serializers.Serializer):
    """Serialiser for limit param in the home page endpoint query string."""

    limit = serializers.IntegerField(min_value=1, default=5)
