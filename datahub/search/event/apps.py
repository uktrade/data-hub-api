from datahub.event.models import Event as DBEvent
from datahub.search.apps import SearchApp
from datahub.search.event.models import Event


class EventSearchApp(SearchApp):
    """SearchApp for events."""

    name = 'event'
    es_model = Event
    view_permissions = ('event.view_event',)
    queryset = DBEvent.objects.select_related(
        'address_country',
        'event_type',
        'location_type',
        'organiser',
        'lead_team',
        'uk_region',
        'service',
    ).prefetch_related(
        'related_programmes',
        'teams',
    )
