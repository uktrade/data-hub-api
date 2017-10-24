from rest_framework import serializers

from ..serializers import (
    DateTimeyField,
    SearchSerializer,
    SingleOrListField,
    StringUUIDField,
)


class SearchEventSerializer(SearchSerializer):
    """Serialiser used to validate Event search POST bodies."""

    address_country = SingleOrListField(child=StringUUIDField(), required=False)
    disabled_on_exists = serializers.BooleanField(required=False)
    disabled_on_after = DateTimeyField(required=False)
    disabled_on_before = DateTimeyField(required=False)
    event_type = SingleOrListField(child=StringUUIDField(), required=False)
    lead_team = SingleOrListField(child=StringUUIDField(), required=False)
    name = serializers.CharField(required=False)
    organiser = SingleOrListField(child=StringUUIDField(), required=False)
    organiser_name = serializers.CharField(required=False)
    start_date_after = DateTimeyField(required=False)
    start_date_before = DateTimeyField(required=False)
    teams = SingleOrListField(child=StringUUIDField(), required=False)
    uk_region = SingleOrListField(child=StringUUIDField(), required=False)

    SORT_BY_FIELDS = (
        'id',
        'name',
        'created_on',
        'modified_on',
        'start_date',
        'end_date',
    )
