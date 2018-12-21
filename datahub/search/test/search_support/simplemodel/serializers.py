from rest_framework import serializers

from datahub.search.serializers import SearchSerializer


class SearchSimpleModelSerializer(SearchSerializer):
    """Serialiser used to validate simple model search POST bodies."""

    name = serializers.CharField(required=False)

    SORT_BY_FIELDS = ('name', 'name_normalized_keyword')
