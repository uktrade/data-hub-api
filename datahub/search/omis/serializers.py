from rest_framework import serializers

from datahub.core.serializers import RelaxedDateField, RelaxedDateTimeField
from datahub.search.serializers import (
    EntitySearchSerializer,
    SingleOrListField,
    StringUUIDField,
)


class SearchOrderSerializer(EntitySearchSerializer):
    """Serialiser used to validate OMIS search POST bodies."""

    primary_market = SingleOrListField(child=StringUUIDField(), required=False)
    sector_descends = SingleOrListField(child=StringUUIDField(), required=False)
    uk_region = SingleOrListField(child=StringUUIDField(), required=False)
    # Note that completed_on is a DateTime field, but we only allow filtering using whole dates
    # for simplicity
    # Elasticsearch sets the time component for completed_on_before to 23:59:59.999
    # automatically
    completed_on_before = RelaxedDateField(required=False)
    completed_on_after = RelaxedDateField(required=False)
    created_on_before = RelaxedDateTimeField(required=False)
    created_on_after = RelaxedDateTimeField(required=False)
    delivery_date_before = RelaxedDateField(required=False)
    delivery_date_after = RelaxedDateField(required=False)
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
