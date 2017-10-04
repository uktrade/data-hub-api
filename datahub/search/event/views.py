from datahub.oauth.scopes import Scope
from .models import Event
from .serializers import SearchEventSerializer
from ..views import SearchAPIView, SearchExportAPIView


class SearchEventParams:
    """Search event params."""

    required_scopes = (Scope.internal_front_end,)
    entity = Event
    serializer_class = SearchEventSerializer

    FILTER_FIELDS = (
        'name',
        'organiser',
        'organiser_name',
        'event_type',
        'start_date_after',
        'start_date_before',
        'address_country',
        'uk_region',
    )

    REMAP_FIELDS = {
        'name': 'name_trigram',
        'organiser': 'organiser.id',
        'organiser_name': 'organiser.name_trigram',
        'event_type': 'event_type.id',
        'address_country': 'address_country.id',
        'uk_region': 'uk_region.id',
    }


class SearchEventAPIView(SearchEventParams, SearchAPIView):
    """Filtered event search view."""


class SearchEventExportAPIView(SearchEventParams, SearchExportAPIView):
    """Filtered event search export view."""
