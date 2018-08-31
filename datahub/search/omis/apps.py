from datahub.omis.order.models import Order as DBOrder, OrderPermission
from .models import Order
from .views import SearchOrderAPIView, SearchOrderExportAPIView
from ..apps import SearchApp


class OrderSearchApp(SearchApp):
    """SearchApp for order"""

    name = 'order'
    es_model = Order
    view = SearchOrderAPIView
    export_view = SearchOrderExportAPIView
    view_permissions = (f'order.{OrderPermission.view}',)
    export_permission = f'order.{OrderPermission.export}'
    queryset = DBOrder.objects.select_related(
        'company',
        'contact',
        'created_by',
        'primary_market',
        'sector',
    )
