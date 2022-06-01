from datahub.activity_stream.event.serializers import EventActivitySerializer
from datahub.activity_stream.pagination import ActivityCursorPagination
from datahub.activity_stream.views import ActivityViewSet
from datahub.event.queryset import get_base_event_queryset


class EventCursorPagination(ActivityCursorPagination):
    """
    Cursor pagination for events.
    """

    summary = 'Event'


class EventActivityViewSet(ActivityViewSet):
    """
    Events ViewSet for the activity stream
    """

    pagination_class = EventCursorPagination
    serializer_class = EventActivitySerializer
    queryset = get_base_event_queryset()
