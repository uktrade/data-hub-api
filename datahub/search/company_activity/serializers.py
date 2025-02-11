from rest_framework import serializers

from datahub.core.serializers import RelaxedDateTimeField
from datahub.search.serializers import (
    EntitySearchQuerySerializer,
    SingleOrListField,
    StringUUIDField,
)


class SearchCompanyActivityQuerySerializer(EntitySearchQuerySerializer):
    """Serialiser used to validate company search POST bodies."""

    id = SingleOrListField(child=StringUUIDField(), required=False)

    activity_source = serializers.CharField(required=False)

    company = SingleOrListField(child=StringUUIDField(), required=False)
    company_name = serializers.CharField(required=False)
    interaction = SingleOrListField(child=StringUUIDField(), required=False)
    dit_participants__adviser = SingleOrListField(child=StringUUIDField(), required=False)
    date_after = RelaxedDateTimeField(required=False)
    date_before = RelaxedDateTimeField(required=False)

    subject = serializers.CharField(required=False)

    include_parent_companies = serializers.BooleanField(required=False, default=False)
    include_subsidiary_companies = serializers.BooleanField(required=False, default=False)

    SORT_BY_FIELDS = (
        'date',
        'subject',
    )
