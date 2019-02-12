from rest_framework import serializers

from datahub.search.serializers import (
    EntitySearchQuerySerializer,
    SingleOrListField,
    StringUUIDField,
)


class SearchCompanyQuerySerializer(EntitySearchQuerySerializer):
    """Serialiser used to validate company search POST bodies."""

    archived = serializers.BooleanField(required=False)
    description = serializers.CharField(required=False)
    export_to_country = SingleOrListField(child=StringUUIDField(), required=False)
    future_interest_country = SingleOrListField(child=StringUUIDField(), required=False)
    global_headquarters = SingleOrListField(child=StringUUIDField(), required=False)
    headquarter_type = SingleOrListField(
        child=StringUUIDField(allow_null=True),
        required=False,
        allow_null=True,
    )
    name = serializers.CharField(required=False)
    sector = SingleOrListField(child=StringUUIDField(), required=False)
    sector_descends = SingleOrListField(child=StringUUIDField(), required=False)
    trading_address_country = SingleOrListField(child=StringUUIDField(), required=False)
    country = SingleOrListField(child=StringUUIDField(), required=False)
    uk_based = serializers.BooleanField(required=False)
    uk_region = SingleOrListField(child=StringUUIDField(), required=False)

    SORT_BY_FIELDS = (
        'archived',
        'archived_by',
        'business_type.name',
        'companies_house_data.company_number',
        'company_number',
        'created_on',
        'employee_range.name',
        'headquarter_type.name',
        'id',
        'modified_on',
        'name',
        'registered_address_town',
        'sector.name',
        'trading_address_town',
        'turnover_range.name',
        'uk_based',
        'uk_region.name',
    )
