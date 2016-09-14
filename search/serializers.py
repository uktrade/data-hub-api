"""Search result serializers."""

from rest_framework import serializers


class SearchResultSerializer(serializers.Serializer):
    """Serialize the ES search results."""

    source_id = serializers.CharField(required=False)
