from ..serializers import SearchSerializer


class SearchEventSerializer(SearchSerializer):
    """Serialiser used to validate Event search POST bodies."""

    SORT_BY_FIELDS = (
        'id',
        'name',
        'created_on',
        'modified_on',
    )
