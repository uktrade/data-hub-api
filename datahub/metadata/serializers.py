from rest_framework import serializers

from .models import Country


class NestedCountrySerializer(serializers.ModelSerializer):
    """Nested Country serializer."""

    class Meta:  # noqa: D101
        model = Country
        fields = '__all__'
