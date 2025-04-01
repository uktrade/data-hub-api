from datahub.activity_stream.interaction.serializers import InteractionActivitySerializer
from datahub.activity_stream.pagination import ActivityCursorPagination
from datahub.activity_stream.views import ActivityViewSet
from datahub.interaction.queryset import get_base_interaction_queryset


class InteractionCursorPagination(ActivityCursorPagination):
    """Cursor pagination for interaction."""

    summary = 'Interaction Activities'


class InteractionActivityViewSet(ActivityViewSet):
    """Interaction ViewSet for the activity stream."""

    pagination_class = InteractionCursorPagination
    serializer_class = InteractionActivitySerializer
    queryset = get_base_interaction_queryset()
