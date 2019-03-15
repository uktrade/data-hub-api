from rest_framework.serializers import CharField, IntegerField

from datahub.core.serializers import RelaxedDateTimeField
from datahub.search.serializers import (
    EntitySearchQuerySerializer,
    SingleOrListField,
    StringUUIDField,
)


class SearchLargeInvestorProfileQuerySerializer(EntitySearchQuerySerializer):
    """Serializer used to validate investor profile search POST bodies."""

    id = SingleOrListField(
        child=StringUUIDField(),
        required=False,
    )

    # Main filters
    asset_classes_of_interest = SingleOrListField(
        child=StringUUIDField(),
        required=False,
    )
    country_of_origin = SingleOrListField(
        child=StringUUIDField(),
        required=False,
    )
    investor_company = SingleOrListField(
        child=StringUUIDField(),
        required=False,
    )
    investor_company_name = CharField(required=False)
    created_by = SingleOrListField(
        child=StringUUIDField(),
        required=False,
    )

    # Detail filters
    investor_type = SingleOrListField(
        child=StringUUIDField(),
        required=False,
    )
    required_checks_conducted = SingleOrListField(
        child=StringUUIDField(),
        required=False,
    )
    global_assets_under_management_start = IntegerField(required=False)
    global_assets_under_management_end = IntegerField(required=False)
    investable_capital_start = IntegerField(required=False)
    investable_capital_end = IntegerField(required=False)

    # Requirement filters
    deal_ticket_size = SingleOrListField(
        child=StringUUIDField(),
        required=False,
    )
    investment_type = SingleOrListField(
        child=StringUUIDField(),
        required=False,
    )
    minimum_return_rate = SingleOrListField(
        child=StringUUIDField(),
        required=False,
    )
    time_horizon = SingleOrListField(
        child=StringUUIDField(),
        required=False,
    )
    restriction = SingleOrListField(
        child=StringUUIDField(),
        required=False,
    )
    construction_risk = SingleOrListField(
        child=StringUUIDField(),
        required=False,
    )
    minimum_equity_percentage = SingleOrListField(
        child=StringUUIDField(),
        required=False,
    )
    desired_deal_role = SingleOrListField(
        child=StringUUIDField(),
        required=False,
    )

    # Location filters
    uk_region_location = SingleOrListField(
        child=StringUUIDField(),
        required=False,
    )
    other_countries_being_considered = SingleOrListField(
        child=StringUUIDField(),
        required=False,
    )

    # Extra filters
    created_on_after = RelaxedDateTimeField(required=False)
    created_on_before = RelaxedDateTimeField(required=False)

    SORT_BY_FIELDS = (
        'created_on',
        'modified_on',
        'investor_company.name',
        'global_assets_under_management',
        'investable_capital',
    )
