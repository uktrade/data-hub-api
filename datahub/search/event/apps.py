from datahub.event.models import Event as DBEvent
from datahub.search.apps import SearchApp
from datahub.search.event.models import Event
from datahub.search.event.views import SearchEventAPIView


class EventSearchApp(SearchApp):
    """SearchApp for events."""

    name = 'event'
    ESModel = Event
    view = SearchEventAPIView
    queryset = DBEvent.objects.prefetch_related(
        'address_country',
        'location_type',
        'organiser'
        'lead_team',
        'related_programmes',
        'teams',
    )
