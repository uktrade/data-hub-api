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
    search_model = Order
    view_permissions = (f'order.{OrderPermission.view}',)
    export_permission = f'order.{OrderPermission.export}'
    queryset = DBOrder.objects.select_related(
        'billing_address_country',
        'cancellation_reason',
        'cancelled_by',
        'company',
        'completed_by',
        'contact',
        'created_by__dit_team',
        'primary_market',
        'sector__parent__parent',
        'uk_region',
    ).prefetch_related(
        'service_types',
        Prefetch('assignees', queryset=OrderAssignee.objects.select_related('adviser__dit_team')),
        Prefetch(
            'subscribers',
            queryset=OrderSubscriber.objects.select_related('adviser__dit_team'),
        ),
    )
