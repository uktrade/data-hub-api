from rest_framework import serializers

from ..serializers import (
    RelaxedDateTimeField,
    SearchSerializer,
    SingleOrListField,
    StringUUIDField,
)


class SearchOrderSerializer(SearchSerializer):
    """Serialiser used to validate OMIS search POST bodies."""

    primary_market = SingleOrListField(child=StringUUIDField(), required=False)
    uk_region = SingleOrListField(child=StringUUIDField(), required=False)
    created_on_before = RelaxedDateTimeField(required=False)
    created_on_after = RelaxedDateTimeField(required=False)
    assigned_to_adviser = SingleOrListField(child=StringUUIDField(), required=False)
    assigned_to_team = SingleOrListField(child=StringUUIDField(), required=False)
    status = SingleOrListField(child=serializers.CharField(), required=False)
    reference = SingleOrListField(child=serializers.CharField(), required=False)
    total_cost = serializers.IntegerField(required=False)
    subtotal_cost = serializers.IntegerField(required=False)
    contact_name = serializers.CharField(required=False)
    company = SingleOrListField(child=StringUUIDField(), required=False)
    company_name = serializers.CharField(required=False)

    DEFAULT_ORDERING = 'created_on:desc'

    SORT_BY_FIELDS = (
        'created_on',
        'modified_on',
        'delivery_date',
        'payment_due_date',
    )
