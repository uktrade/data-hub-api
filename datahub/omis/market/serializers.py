from rest_framework import serializers


class MarketSerializer(serializers.Serializer):
    """OMIS Market serializer."""

    id = serializers.ReadOnlyField(source='country_id')
    name = serializers.ReadOnlyField(source='country.name')
    disabled_on = serializers.ReadOnlyField()

    class Meta:  # noqa: D101
        fields = '__all__'
