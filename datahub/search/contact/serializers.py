from rest_framework import serializers

from ..serializers import (
    SearchSerializer,
    SingleOrListField,
    StringUUIDField,
)


class SearchContactSerializer(SearchSerializer):
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
        'adviser.name',
        'archived',
        'archived_on',
        'archived_by.name',
        'company.name',
        'contactable_by_dit',
        'contactable_by_uk_dit_partners',
        'contactable_by_overseas_dit_partners',
        'accepts_dit_email_marketing',
        'contactable_by_email',
        'contactable_by_phone',
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
