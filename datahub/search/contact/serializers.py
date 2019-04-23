from rest_framework import serializers

from datahub.search.serializers import (
    EntitySearchQuerySerializer,
    SingleOrListField,
    StringUUIDField,
)


class SearchContactQuerySerializer(EntitySearchQuerySerializer):
    """Serialiser used to validate contact search POST bodies."""

    archived = serializers.BooleanField(required=False)
    name = serializers.CharField(required=False)
    company = SingleOrListField(child=StringUUIDField(), required=False)
    company_name = serializers.CharField(required=False)
    company_sector = SingleOrListField(child=StringUUIDField(), required=False)
    company_sector_descends = SingleOrListField(child=StringUUIDField(), required=False)
    company_uk_region = SingleOrListField(child=StringUUIDField(), required=False)
    address_country = SingleOrListField(child=StringUUIDField(), required=False)
    created_by = SingleOrListField(child=StringUUIDField(), required=False)
    created_on_exists = serializers.BooleanField(required=False)

    SORT_BY_FIELDS = (
        'address_country.name',
        'address_county',
        'address_same_as_company',
        'address_town',
        'adviser.name.keyword',
        'archived',
        'archived_on',
        'archived_by.name.keyword',
        'company.name',
        'accepts_dit_email_marketing',
        'created_on',
        'email',
        'first_name',
        'id',
        'job_title',
        'last_name',
        'modified_on',
        'name',
        'primary',
        'telephone_countrycode',
        'telephone_number',
        'title.name',
        'company_sector.name',
    )
