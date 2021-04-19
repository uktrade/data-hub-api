from rest_framework.serializers import CharField, IntegerField

from datahub.core.serializers import RelaxedDateTimeField
from datahub.search.serializers import (
    EntitySearchQuerySerializer,
    SingleOrListField,
    StringUUIDField,
)


class SearchLargeCapitalOpportunityQuerySerializer(EntitySearchQuerySerializer):
    """Serializer used to validate large capital opportunity search POST bodies."""

    id = SingleOrListField(
        child=StringUUIDField(),
        required=False,
    )

    # Main filters
    type = SingleOrListField(
        child=StringUUIDField(),
        required=False,
    )
    status = SingleOrListField(
        child=StringUUIDField(),
        required=False,
    )
    name = CharField(required=False)

    created_by = SingleOrListField(
        child=StringUUIDField(),
        required=False,
    )

    # Detail filters
    uk_region_location = SingleOrListField(
        child=StringUUIDField(),
        required=False,
    )
    promoter = SingleOrListField(
        child=StringUUIDField(),
        required=False,
    )
    promoter_name = CharField(required=False)
    lead_dit_relationship_manager = SingleOrListField(
        child=StringUUIDField(),
        required=False,
    )
    required_checks_conducted = SingleOrListField(
        child=StringUUIDField(),
        required=False,
    )
    required_checks_conducted_by = SingleOrListField(
        child=StringUUIDField(),
        required=False,
    )

    asset_class = SingleOrListField(
        child=StringUUIDField(),
        required=False,
    )
    opportunity_value_type = SingleOrListField(
        child=StringUUIDField(),
        required=False,
    )
    opportunity_value_start = IntegerField(required=False)
    opportunity_value_end = IntegerField(required=False)
    construction_risk = SingleOrListField(
        child=StringUUIDField(),
        required=False,
    )

    # Requirement filters
    total_investment_sought_start = IntegerField(required=False)
    total_investment_sought_end = IntegerField(required=False)
    current_investment_secured_start = IntegerField(required=False)
    current_investment_secured_end = IntegerField(required=False)
    investment_type = SingleOrListField(
        child=StringUUIDField(),
        required=False,
    )
    estimated_return_rate = SingleOrListField(
        child=StringUUIDField(),
        required=False,
    )
    time_horizon = SingleOrListField(
        child=StringUUIDField(),
        required=False,
    )

    # Extra filters
    created_on_after = RelaxedDateTimeField(required=False)
    created_on_before = RelaxedDateTimeField(required=False)

    SORT_BY_FIELDS = (
        'created_on',
        'modified_on',
        'name',
    )
