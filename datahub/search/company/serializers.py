from rest_framework import serializers

from datahub.search.serializers import (
    AutocompleteSearchSerializer,
    EntitySearchQuerySerializer,
    IdNameSerializer,
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


class AutocompleteSearchCompanySerializer(AutocompleteSearchSerializer):
    """Autocomplete search serializer for companies."""

    name = serializers.CharField()
    trading_name = serializers.CharField()
    trading_names = serializers.ListField(child=serializers.CharField(), required=False)
    trading_address_1 = serializers.CharField()
    trading_address_2 = serializers.CharField()
    trading_address_town = serializers.CharField()
    trading_address_county = serializers.CharField()
    trading_address_country = IdNameSerializer()
    trading_address_postcode = serializers.CharField()
    registered_address_1 = serializers.CharField()
    registered_address_2 = serializers.CharField()
    registered_address_town = serializers.CharField()
    registered_address_county = serializers.CharField()
    registered_address_country = IdNameSerializer()
    registered_address_postcode = serializers.CharField()
