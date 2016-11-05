from rest_framework import serializers

from company.serializers import NestedContactSerializer, NestedInteractionSerializer


class IntelligentHomepageSerializer(serializers.Serializer):
    """Intelligent homepage serializer."""

    interactions = NestedInteractionSerializer(many=True)
    contacts = NestedContactSerializer(many=True)
