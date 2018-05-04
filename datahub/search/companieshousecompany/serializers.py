from rest_framework import serializers

from datahub.core.serializers import RelaxedDateTimeField
from ..serializers import (
    SearchSerializer,
    SingleOrListField,
)


class SearchCompaniesHouseCompanySerializer(SearchSerializer):
    """Serialiser used to validate companies house company POST bodies."""

    name = serializers.CharField(required=False)
    company_number = serializers.CharField(required=False)
    company_status = SingleOrListField(child=serializers.CharField(), required=False)
    incorporation_date_after = RelaxedDateTimeField(required=False)
    incorporation_date_before = RelaxedDateTimeField(required=False)

    SORT_BY_FIELDS = (
        'incorporation_date',
        'name',
    )
