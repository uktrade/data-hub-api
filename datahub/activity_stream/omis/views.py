from django.db.models import Prefetch

from datahub.activity_stream.omis.serializers import OMISOrderAddedSerializer
from datahub.activity_stream.pagination import ActivityCursorPagination
from datahub.activity_stream.views import ActivityViewSet
from datahub.omis.order.models import Order, OrderAssignee


class OMISOrderAddedPagination(ActivityCursorPagination):
    """
    OMIS Order added pagination for activity stream.
    """

    ordering = ('created_on', 'id')
    summary = 'OMIS Order Added Activity'


class OMISOrderAddedViewSet(ActivityViewSet):
    """
    OMIS Order added ViewSet for activity stream.
    """

    pagination_class = OMISOrderAddedPagination
    serializer_class = OMISOrderAddedSerializer
    queryset = Order.objects.select_related(
        'company',
        'contact',
        'created_by',
        'primary_market',
        'uk_region',
    ).prefetch_related(
        Prefetch('assignees', queryset=OrderAssignee.objects.order_by('pk')),
    )
