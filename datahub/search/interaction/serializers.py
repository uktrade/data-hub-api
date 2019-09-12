from rest_framework import serializers

from datahub.core.serializers import RelaxedDateTimeField
from datahub.search.serializers import (
    EntitySearchQuerySerializer,
    SingleOrListField,
    StringUUIDField,
)
from datahub.search.utils import SearchOrdering, SortDirection


class SearchInteractionQuerySerializer(EntitySearchQuerySerializer):
    """Serialiser used to validate interaction search POST bodies."""

    kind = SingleOrListField(child=serializers.CharField(), required=False)
    company = SingleOrListField(child=StringUUIDField(), required=False)
    company_name = serializers.CharField(required=False)
    company_one_list_group_tier = SingleOrListField(child=StringUUIDField(), required=False)
    date_after = RelaxedDateTimeField(required=False)
    date_before = RelaxedDateTimeField(required=False)
    created_on_exists = serializers.BooleanField(required=False)
    dit_participants__adviser = SingleOrListField(child=StringUUIDField(), required=False)
    dit_participants__team = SingleOrListField(child=StringUUIDField(), required=False)
    communication_channel = SingleOrListField(child=StringUUIDField(), required=False)
    investment_project = SingleOrListField(child=StringUUIDField(), required=False)
    policy_areas = SingleOrListField(child=StringUUIDField(), required=False)
    policy_issue_types = SingleOrListField(child=StringUUIDField(), required=False)
    service = SingleOrListField(child=StringUUIDField(), required=False)
    sector_descends = SingleOrListField(child=StringUUIDField(), required=False)
    was_policy_feedback_provided = serializers.BooleanField(required=False)

    DEFAULT_ORDERING = SearchOrdering('date', SortDirection.desc)

    SORT_BY_FIELDS = (
        'company.name',
        'date',
        'subject',
    )
