from rest_framework import serializers

from datahub.core.serializers import NestedRelatedField

from .models import Country, TeamRole, UKRegion


class NestedCountrySerializer(serializers.ModelSerializer):
    """Nested Country serializer."""

    class Meta:  # noqa: D101
        model = Country
        fields = '__all__'


class TeamSerializer(serializers.Serializer):
    """Team serializer."""

    id = serializers.ReadOnlyField()
    name = serializers.ReadOnlyField()
    role = NestedRelatedField(TeamRole, read_only=True)
    uk_region = NestedRelatedField(UKRegion, read_only=True)
    country = NestedRelatedField(Country, read_only=True)

    class Meta:  # noqa: D101
        fields = '__all__'


class CountrySerializer(serializers.Serializer):
    """Country serializer."""

    id = serializers.ReadOnlyField()
    name = serializers.ReadOnlyField()
    omis_disabled_on = serializers.ReadOnlyField()

    class Meta:  # noqa: D101
        fields = '__all__'
