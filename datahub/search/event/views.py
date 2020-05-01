from datahub.search.event import EventSearchApp
from datahub.search.event.serializers import SearchEventQuerySerializer
from datahub.search.views import register_v3_view, SearchAPIView


class SearchEventAPIViewMixin:
    """Defines common settings."""

    search_app = EventSearchApp
    serializer_class = SearchEventQuerySerializer
    es_sort_by_remappings = {
        'name': 'name.keyword',
    }

    FILTER_FIELDS = (
        'address_country',
        'disabled_on',
        'disabled_on_exists',
        'event_type',
        'lead_team',
        'name',
        'organiser',
        'organiser_name',
        'start_date_after',
        'start_date_before',
        'teams',
        'uk_region',
    )

    REMAP_FIELDS = {
        'address_country': 'address_country.id',
        'event_type': 'event_type.id',
        'lead_team': 'lead_team.id',
        'organiser': 'organiser.id',
        'teams': 'teams.id',
        'uk_region': 'uk_region.id',
    }

    COMPOSITE_FILTERS = {
        'name': ['name', 'name.trigram'],
        'organiser_name': ['organiser.name', 'organiser.name.trigram'],
    }


@register_v3_view()
class SearchEventAPIView(SearchEventAPIViewMixin, SearchAPIView):
    """Filtered event search view."""
