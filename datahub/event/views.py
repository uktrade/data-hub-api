from datahub.core.viewsets import CoreViewSetV3
from datahub.event.models import Event
from datahub.event.serializers import EventSerializer


class EventViewSet(CoreViewSetV3):
    """Views for events."""

    serializer_class = EventSerializer
    queryset = Event.objects.select_related(
        'address_country'
    ).prefetch_related(
        'additional_teams',
        'related_programmes',
    )
