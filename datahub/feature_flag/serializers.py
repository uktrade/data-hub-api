from rest_framework import serializers

from datahub.feature_flag.models import FeatureFlag


class FeatureFlagSerializer(serializers.ModelSerializer):
    """Feature flag serialiser."""

    code = serializers.CharField()
    is_active = serializers.BooleanField()

    class Meta:
        model = FeatureFlag
        fields = (
            'code',
            'is_active',
        )
        read_only_fields = fields
