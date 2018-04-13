from rest_framework import serializers

from datahub.feature_flag.models import FeatureFlag


class FeatureFlagSerializer(serializers.ModelSerializer):
    """Feature flag serializer."""

    code = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = FeatureFlag
        fields = (
            'code',
            'description',
            'is_active',
        )
        read_only_fields = fields
