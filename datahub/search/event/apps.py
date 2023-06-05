from datahub.event.models import Event as DBEvent
from datahub.search.apps import SearchApp
from datahub.search.event.models import Event


class EventSearchApp(SearchApp):
    """SearchApp for events."""

    name = 'event'
    search_model = Event
    view_permissions = ('event.view_event',)
    queryset = DBEvent.objects.select_related(
        'address_country',
        'event_type',
        'location_type',
        'organiser',
        'lead_team',
        'uk_region',
        'service',
        'related_programmes',
    ).prefetch_related(
        'teams',
    )
