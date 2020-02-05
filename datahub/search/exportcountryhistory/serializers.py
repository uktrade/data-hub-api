from logging import getLogger

from django.utils.translation import gettext_lazy

from datahub.search.serializers import (
    EntitySearchQuerySerializer,
    SingleOrListField,
    StringUUIDField,
)

logger = getLogger(__name__)


class SearchExportCountryHistorySerializer(EntitySearchQuerySerializer):
    """Serializer used to validate ExportCountryHistory search POST bodies."""

    default_error_messages = {
        'no_empty_field': gettext_lazy(
            'Request must include either country or company parameters',
        ),
    }

    # TODO: re-enable these once the history_date field is updated
    # DEFAULT_ORDERING = SearchOrdering('history_date', SortDirection.desc)

    # SORT_BY_FIELDS = (
    #     'history_date',
    # )

    country = SingleOrListField(child=StringUUIDField(), required=False)
    company = SingleOrListField(child=StringUUIDField(), required=False)

    # def validate(self, data):
    #     """Serializer should have at least one parameter"""
    #     if 'country' not in data and 'company' not in data:
    #         raise serializers.ValidationError(
    #             self.error_messages['no_empty_field'],
    #         )
    #
    #     return data
