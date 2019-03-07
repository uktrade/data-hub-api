from django.db.models import Prefetch

from datahub.omis.order.models import (
    Order as DBOrder,
    OrderAssignee,
    OrderPermission,
    OrderSubscriber,
)
from datahub.search.apps import SearchApp
from datahub.search.omis.models import Order


class OrderSearchApp(SearchApp):
    """SearchApp for order"""

    name = 'order'
    es_model = Order
    view_permissions = (f'order.{OrderPermission.view}',)
    export_permission = f'order.{OrderPermission.export}'
    queryset = DBOrder.objects.select_related(
        'company',
        'contact',
        'created_by',
        'primary_market',
        'sector',
    ).prefetch_related(
        'service_types',
        Prefetch('assignees', queryset=OrderAssignee.objects.select_related('adviser__dit_team')),
        Prefetch(
            'subscribers',
            queryset=OrderSubscriber.objects.select_related('adviser__dit_team'),
        ),
    )
