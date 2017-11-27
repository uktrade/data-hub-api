from rest_framework import serializers


class LimitParamSerializer(serializers.Serializer):
    """Serialiser for limit param in the home page endpoint query string."""

    limit = serializers.IntegerField(min_value=1, default=5)
