from datahub.activity_stream.interaction.serializers import InteractionActivitySerializer
from datahub.activity_stream.pagination import ActivityCursorPagination
from datahub.activity_stream.views import ActivityViewSet
from datahub.interaction.queryset import get_base_interaction_queryset


class InteractionCursorPagination(ActivityCursorPagination):
    """
    Cursor pagination for interaction.

    `modified_on` is no unchanging but we have decided to use it because the benefits of being
    able to generate the last page of interactions in under 10s far outweigh the fact that
    sometimes the last page will not contain all the updates.
    """

    ordering = ('modified_on', 'pk')
    summary = 'Interaction Activities'


class InteractionActivityViewSet(ActivityViewSet):
    """
    Interaction ViewSet for the activity stream
    """

    pagination_class = InteractionCursorPagination
    serializer_class = InteractionActivitySerializer
    queryset = get_base_interaction_queryset()
