from datahub.oauth.scopes import Scope
from datahub.search.event.models import Event
from datahub.search.event.serializers import SearchEventSerializer
from datahub.search.views import SearchAPIView


class SearchEventParams:
    """Search event params."""

    required_scopes = (Scope.internal_front_end,)
    entity = Event
    serializer_class = SearchEventSerializer

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
        'organiser_name': ['organiser.name', 'organiser.name_trigram'],
    }


class SearchEventAPIView(SearchEventParams, SearchAPIView):
    """Filtered event search view."""
