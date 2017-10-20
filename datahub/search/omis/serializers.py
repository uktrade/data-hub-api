from ..serializers import SearchSerializer


class SearchOrderSerializer(SearchSerializer):
    """Serialiser used to validate OMIS search POST bodies."""

    DEFAULT_ORDERING = 'created_on:desc'

    SORT_BY_FIELDS = (
        'created_on',
        'modified_on',
        'delivery_date',
        'payment_due_date',
    )
