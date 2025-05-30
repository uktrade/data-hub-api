from rest_framework import serializers

from datahub.core.serializers import RelaxedDateTimeField
from datahub.search.serializers import (
    EntitySearchQuerySerializer,
    SingleOrListField,
    StringUUIDField,
)


class NestedDisabledOnQuerySerializer(serializers.Serializer):
    """Serialiser used to validate disabled_on filter.

    Validated data uses "or" operator. For example if you want to
    find events that were disabled after certain date, but also those that
    have not been disabled.
    """

    exists = serializers.BooleanField(required=False)
    after = RelaxedDateTimeField(required=False)


class SearchEventQuerySerializer(EntitySearchQuerySerializer):
    """Serialiser used to validate Event search POST bodies.

    Nested disabled_on filters use "or" operator. For example if you want to
    find events that were disabled after certain date, but also those that
    have not been disabled.
    """

    address_country = SingleOrListField(child=StringUUIDField(), required=False)
    disabled_on = NestedDisabledOnQuerySerializer(required=False)
    disabled_on_exists = serializers.BooleanField(required=False)
    event_type = SingleOrListField(child=StringUUIDField(), required=False)
    lead_team = SingleOrListField(child=StringUUIDField(), required=False)
    name = serializers.CharField(required=False)
    organiser = SingleOrListField(child=StringUUIDField(), required=False)
    organiser_name = serializers.CharField(required=False)
    related_programmes = SingleOrListField(child=StringUUIDField(), required=False)
    start_date_after = RelaxedDateTimeField(required=False)
    start_date_before = RelaxedDateTimeField(required=False)
    teams = SingleOrListField(child=StringUUIDField(), required=False)
    uk_region = SingleOrListField(child=StringUUIDField(), required=False)
    stova_event = SingleOrListField(child=StringUUIDField(), required=False)

    SORT_BY_FIELDS = (
        'id',
        'name',
        'created_on',
        'modified_on',
        'start_date',
        'end_date',
    )
