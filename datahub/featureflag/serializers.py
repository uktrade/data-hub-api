from rest_framework import serializers

from datahub.company.serializers import NestedAdviserField
from datahub.core.serializers import ConstantModelSerializer


class FeatureFlagSerializer(ConstantModelSerializer):
    """Feature flag serializer."""

    description = serializers.CharField(read_only=True)
    created_on = serializers.DateTimeField(read_only=True)
    modified_on = serializers.DateTimeField(read_only=True)
    created_by = NestedAdviserField(read_only=True)
    modified_by = NestedAdviserField(read_only=True)
