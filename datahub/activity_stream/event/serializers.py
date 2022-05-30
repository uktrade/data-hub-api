from datahub.activity_stream.serializers import ActivitySerializer
from datahub.event.models import Event


class EventActivitySerializer(ActivitySerializer):
    """Events serialiser for activity stream."""

    class Meta:
        model = Event
