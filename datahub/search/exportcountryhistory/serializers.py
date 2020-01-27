from logging import getLogger

from django.utils.translation import gettext_lazy
from rest_framework import serializers

from datahub.core.serializers import RelaxedDateTimeField
from datahub.search.serializers import (
    EntitySearchQuerySerializer,
    SingleOrListField,
    StringUUIDField,
)
from datahub.search.utils import SearchOrdering, SortDirection

logger = getLogger(__name__)


class SearchExportCountryHistorySerializer(EntitySearchQuerySerializer):
    """Serializer used to validate ExportCountryHistory search POST bodies."""

    default_error_messages = {
        'no_empty_field': gettext_lazy(
            'Request must include either country or company parameters',
        ),
    }

    DEFAULT_ORDERING = SearchOrdering('history_date', SortDirection.desc)

    SORT_BY_FIELDS = (
        'history_date',
        'country',
        'company',
    )

    history_user = SingleOrListField(child=StringUUIDField(), required=False)
    country = SingleOrListField(child=StringUUIDField(), required=False)
    company = SingleOrListField(child=StringUUIDField(), required=False)
    history_date = RelaxedDateTimeField(required=False)

    def validate(self, data):
        """Serializer should have at least one parameter"""
        if 'country' not in data and 'company' not in data:
            raise serializers.ValidationError(
                self.error_messages['no_empty_field'],
            )

        return data
