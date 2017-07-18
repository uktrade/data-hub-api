from datahub.core.viewsets import CoreViewSetV3

from .models import Order
from .serializers import OrderSerializer


class OrderViewSet(CoreViewSetV3):
    """Order ViewSet"""

    serializer_class = OrderSerializer
    queryset = Order.objects.select_related(
        'company',
        'contact',
        'primary_market',
    )
