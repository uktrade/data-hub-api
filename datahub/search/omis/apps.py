from datahub.omis.order.models import Order as DBOrder
from .models import Order
from .views import SearchOrderAPIView
from ..apps import SearchApp


class OrderSearchApp(SearchApp):
    """SearchApp for order"""

    name = 'order'
    es_model = Order
    view = SearchOrderAPIView
    permission_required = ('order.read_order',)
    queryset = DBOrder.objects.select_related(
        'company',
        'contact',
        'created_by',
        'primary_market',
        'sector',
    )
