from rest_framework import serializers

from datahub.core.serializers import NestedRelatedField

from .models import Country, TeamRole, UKRegion


class TeamSerializer(serializers.Serializer):
    """Team serializer."""

    id = serializers.ReadOnlyField()
    name = serializers.ReadOnlyField()
    role = NestedRelatedField(TeamRole, read_only=True)
    uk_region = NestedRelatedField(UKRegion, read_only=True)
    country = NestedRelatedField(Country, read_only=True)

    class Meta:  # noqa: D101
        fields = '__all__'
