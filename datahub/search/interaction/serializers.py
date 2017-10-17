from ..serializers import SearchSerializer


class SearchInteractionSerializer(SearchSerializer):
    """Serialiser used to validate interaction search POST bodies."""

    DEFAULT_ORDERING = 'date:desc'

    SORT_BY_FIELDS = (
        'company.name',
        'contact.name',
        'date',
        'dit_adviser.name',
        'dit_team.name',
        'id',
        'subject',
    )
