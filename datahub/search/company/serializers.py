from rest_framework import serializers

from datahub.search.serializers import (
    EntitySearchQuerySerializer,
    SingleOrListField,
    StringUUIDField,
)


class SearchCompanyQuerySerializer(EntitySearchQuerySerializer):
    """Serialiser used to validate company search POST bodies."""

    archived = serializers.BooleanField(required=False)
    headquarter_type = SingleOrListField(
        child=StringUUIDField(allow_null=True),
        required=False,
        allow_null=True,
    )
    name = serializers.CharField(required=False)
    sector_descends = SingleOrListField(child=StringUUIDField(), required=False)
    country = SingleOrListField(child=StringUUIDField(), required=False)
    uk_based = serializers.BooleanField(required=False)
    uk_region = SingleOrListField(child=StringUUIDField(), required=False)
    future_interest_countries = SingleOrListField(child=StringUUIDField(), required=False)

    SORT_BY_FIELDS = (
        'modified_on',
        'name',
    )


class PublicSearchCompanyQuerySerializer(EntitySearchQuerySerializer):
    """Serialiser used to validate public company search POST bodies."""

    archived = serializers.BooleanField(required=False)
    name = serializers.CharField(required=False)


class AutcompleteSearchCompanyQueryContextSerializer(serializers.Serializer):
    """Serializer used for the additional context filters for company autocomplete search."""

    country = SingleOrListField(
        child=StringUUIDField(allow_null=False), required=False,
    )
