from datahub.omis.order.models import Order as DBOrder

from .models import Order

from ..apps import SearchApp


class OrderSearchApp(SearchApp):
    """SearchApp for order"""

    name = 'order'
    plural_name = 'orders'
    ESModel = Order
    DBModel = DBOrder
    view = None
