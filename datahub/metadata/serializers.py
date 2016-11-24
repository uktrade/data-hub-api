from rest_framework import serializers

from .models import Country, Team


class NestedCountrySerializer(serializers.ModelSerializer):
    """Nested Country serializer."""

    class Meta:  # noqa: D101
        model = Country


class NestedTeamSerializer(serializers.ModelSerializer):
    """Nested Team serializer."""

    class Meta:  # noqa: D101
        model = Team
