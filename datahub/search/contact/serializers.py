from logging import getLogger

from rest_framework import serializers

from datahub.search.serializers import (
    EntitySearchQuerySerializer,
    SingleOrListField,
    StringUUIDField,
)


logger = getLogger(__name__)


class SearchContactQuerySerializer(EntitySearchQuerySerializer):
    """Serialiser used to validate contact search POST bodies."""

    archived = serializers.BooleanField(required=False)
    email = serializers.CharField(required=False)
    name = serializers.CharField(required=False)
    company = SingleOrListField(child=StringUUIDField(), required=False)
    company_name = serializers.CharField(required=False)
    company_sector = SingleOrListField(child=StringUUIDField(), required=False)
    company_sector_descends = SingleOrListField(child=StringUUIDField(), required=False)
    company_uk_region = SingleOrListField(child=StringUUIDField(), required=False)
    address_country = SingleOrListField(child=StringUUIDField(), required=False)
    address_area = SingleOrListField(child=StringUUIDField(), required=False)
    created_by = SingleOrListField(child=StringUUIDField(), required=False)
    created_on_exists = serializers.BooleanField(required=False)
    valid_email = serializers.BooleanField(required=False)

    SORT_BY_FIELDS = (
        'address_country.name',
        'address_area.name',
        'company.name',
        'created_on',
        'last_name',
        'modified_on',
    )
