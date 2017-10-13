from datahub.oauth.scopes import Scope
from datahub.omis.order.models import Order
from datahub.omis.order.views import BaseNestedOrderViewSet

from .models import Payment
from .serializers import PaymentSerializer


class BasePaymentViewSet(BaseNestedOrderViewSet):
    """Base Payment ViewSet."""

    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    pagination_class = None

    def get_queryset(self):
        """
        :returns: the queryset with payments related to the order.
        """
        return super().get_queryset().filter(order=self.get_order())


class PaymentViewSet(BasePaymentViewSet):
    """Payment ViewSet."""

    required_scopes = (Scope.internal_front_end,)


class PublicPaymentViewSet(BasePaymentViewSet):
    """ViewSet for public facing API."""

    required_scopes = (Scope.public_omis_front_end,)

    order_lookup_field = 'public_token'
    order_lookup_url_kwarg = 'public_token'
    order_queryset = Order.objects.publicly_accessible()
