from oauth2_provider.contrib.rest_framework.permissions import IsAuthenticatedOrTokenHasScope
from rest_framework import status
from rest_framework.response import Response

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

    def create_list(self, request, *args, **kwargs):
        """Create a list of payments."""
        serializer = self.get_serializer(
            data=request.data,
            many=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class PublicPaymentViewSet(BasePaymentViewSet):
    """ViewSet for public facing API."""

    permission_classes = (IsAuthenticatedOrTokenHasScope,)
    required_scopes = (Scope.public_omis_front_end,)

    order_lookup_field = 'public_token'
    order_lookup_url_kwarg = 'public_token'
    order_queryset = Order.objects.publicly_accessible()
