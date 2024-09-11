from datahub.search.company_activity import CompanyActivitySearchApp
from datahub.search.company_activity.serializers import (
    SearchCompanyActivityQuerySerializer,
)
from datahub.search.views import (
    register_v4_view,
    SearchAPIView,
)


class SearchCompanyActivityAPIViewMixin:
    """Defines common settings."""

    search_app = CompanyActivitySearchApp
    serializer_class = SearchCompanyActivityQuerySerializer
    es_sort_by_remappings = {
        'name': 'name.keyword',
    }
    fields_to_exclude = (
    )

    FILTER_FIELDS = (
        'id',
        'date_after',
        'date_before',
        'interaction',
        'company',
        'company_name',
        'activity_source',
        'dit_participants__adviser',
    )

    REMAP_FIELDS = {
        'company': 'company.id',
        'interaction': 'interaction.id',
    }

    COMPOSITE_FILTERS = {
        'company_name': [
            'company.name',  # to find 2-letter words
            'company.name.trigram',
            'company.trading_names',  # to find 2-letter words
            'company.trading_names.trigram',
        ],
        'dit_participants__adviser': [
            'interaction.dit_participants.adviser.id',
            'referral.recipient.id',
            'referral.created_by.id',
        ],
    }


@register_v4_view()
class SearchCompanyActivityAPIView(SearchCompanyActivityAPIViewMixin, SearchAPIView):
    """Filtered company search view."""
