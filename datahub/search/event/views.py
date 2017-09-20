from .models import Event
from .serializers import SearchEventSerializer
from ..views import SearchAPIView


class SearchEventAPIView(SearchAPIView):
    """Filtered event search view."""

    entity = Event
    serializer_class = SearchEventSerializer

    FILTER_FIELDS = (
        'name',
        'organiser_name',
        'event_type',
        'start_date_after',
        'start_date_before',
        'address_country',
    )

    REMAP_FIELDS = {
        'name': 'name_trigram',
        'organiser_name': 'organiser.name_trigram',
        'event_type': 'event_type.id',
        'address_country': 'address_country.id',
    }
