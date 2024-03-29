from rest_framework import serializers

from datahub.search.serializers import EntitySearchQuerySerializer


class SearchSimpleModelSerializer(EntitySearchQuerySerializer):
    """Serialiser used to validate simple model search POST bodies."""

    name = serializers.CharField(required=False)
    country = serializers.CharField(required=False)
    archived = serializers.BooleanField(required=False)

    SORT_BY_FIELDS = ('date', 'name')
