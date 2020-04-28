from datahub.core.viewsets import CoreViewSet
from datahub.event.models import Event
from datahub.event.serializers import EventSerializer


class EventViewSet(CoreViewSet):
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
        'service__parent',
    ).prefetch_related(
        'teams',
        'related_programmes',
    )
