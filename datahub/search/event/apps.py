from datahub.event.models import Event as DBEvent
from datahub.search.apps import SearchApp
from datahub.search.event.models import Event
from datahub.search.event.views import SearchEventAPIView, SearchEventExportAPIView


class EventSearchApp(SearchApp):
    """SearchApp for events."""

    name = 'event'
    es_model = Event
    view = SearchEventAPIView
    export_view = SearchEventExportAPIView
    permission_required = ('event.read_event',)
    queryset = DBEvent.objects.prefetch_related(
        'address_country',
        'event_type',
        'location_type',
        'organiser',
        'lead_team',
        'related_programmes',
        'teams',
        'uk_region',
        'service',
    )
