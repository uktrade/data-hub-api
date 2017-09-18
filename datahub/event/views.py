from datahub.core.viewsets import CoreViewSetV3
from datahub.event.models import Event
from datahub.event.serializers import EventSerializer


class EventViewSet(CoreViewSetV3):
    """Views for events."""

    serializer_class = EventSerializer
    queryset = Event.objects.select_related(
        'address_country',
        'event_type',
        'lead_team',
        'location_type',
        'organiser',
        'uk_region',
        'service',
    ).prefetch_related(
        'teams',
        'related_programmes',
    )
