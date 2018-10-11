from datahub.omis.order.models import Order as DBOrder, OrderPermission
from datahub.search.apps import SearchApp
from datahub.search.omis.models import Order
from datahub.search.omis.views import SearchOrderAPIView, SearchOrderExportAPIView


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
