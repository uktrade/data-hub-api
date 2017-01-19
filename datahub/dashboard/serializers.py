from rest_framework import serializers

from datahub.company.serializers import NestedContactSerializer, NestedInteractionSerializer


class IntelligentHomepageSerializer(serializers.Serializer):
    """Intelligent homepage serializer."""

    interactions = NestedInteractionSerializer(many=True)
    contacts = NestedContactSerializer(many=True)

    class Meta:  # noqa: D101
        fields = '__all__'
