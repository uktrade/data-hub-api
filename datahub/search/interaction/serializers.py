from logging import getLogger

from rest_framework import serializers

from datahub.core.serializers import RelaxedDateTimeField
from datahub.search.serializers import (
    EntitySearchQuerySerializer,
    SingleOrListField,
    StringUUIDField,
)
from datahub.search.utils import SearchOrdering, SortDirection

logger = getLogger(__name__)


class SearchInteractionQuerySerializer(EntitySearchQuerySerializer):
    """Serialiser used to validate interaction search POST bodies."""

    kind = SingleOrListField(child=serializers.CharField(), required=False)
    company = SingleOrListField(child=StringUUIDField(), required=False)
    company_name = serializers.CharField(required=False)
    date_after = RelaxedDateTimeField(required=False)
    date_before = RelaxedDateTimeField(required=False)
    created_on_exists = serializers.BooleanField(required=False)
    dit_adviser = SingleOrListField(child=StringUUIDField(), required=False)
    dit_adviser_name = serializers.CharField(required=False)
    dit_team = SingleOrListField(child=StringUUIDField(), required=False)
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
        'contact.name',
        'date',
        'dit_adviser.name',
        'dit_team.name',
        'id',
        'subject',
    )
    deprecated_sortby_fields = {
        'contact.name',
        'dit_adviser.name',
        'dit_team.name',
        'id',
    }

    def validate(self, data):
        """
        Logs all deprecated params to make sure we don't break things when we get rid of them.

        TODO Remove following deprecation period.
        """
        sortby = data.get('sortby')
        if sortby and sortby.field in self.deprecated_sortby_fields:
            logger.error(
                'The following deprecated interaction search sortby field was '
                f'used: {sortby.field}.',
            )
        return super().validate(data)
