from oauth2_provider.contrib.rest_framework.permissions import IsAuthenticatedOrTokenHasScope
from rest_framework.response import Response

from datahub.core.exceptions import APIConflictException
from datahub.oauth.scopes import Scope
from datahub.omis.order.constants import OrderStatus
from datahub.omis.order.models import Order
from datahub.omis.order.views import BaseNestedOrderViewSet
from datahub.omis.payment.models import PaymentGatewaySession
from datahub.omis.payment.serializers import PaymentGatewaySessionSerializer
from datahub.omis.payment.views import BasePaymentViewSet, CreatePaymentGatewaySessionThrottle


class LegacyPublicPaymentViewSet(BasePaymentViewSet):
    """ViewSet for legacy public facing API."""

    permission_classes = (IsAuthenticatedOrTokenHasScope,)
    required_scopes = (Scope.public_omis_front_end,)

    order_lookup_field = 'public_token'
    order_lookup_url_kwarg = 'public_token'
    order_queryset = Order.objects.publicly_accessible()


class LegacyPublicPaymentGatewaySessionViewSet(BaseNestedOrderViewSet):
    """Payment Gateway Session ViewSet for legacy public facing API."""

    permission_classes = (IsAuthenticatedOrTokenHasScope,)
    required_scopes = (Scope.public_omis_front_end,)

    order_lookup_field = 'public_token'
    order_lookup_url_kwarg = 'public_token'
    order_queryset = Order.objects.filter(
        status__in=(
            OrderStatus.QUOTE_ACCEPTED,
            OrderStatus.PAID,
            OrderStatus.COMPLETE,
        ),
    )

    queryset = PaymentGatewaySession.objects.all()
    serializer_class = PaymentGatewaySessionSerializer

    def get_queryset(self):
        """
        :returns: the queryset with session gateway payments for the order.
        """
        return super().get_queryset().filter(order=self.get_order())

    def get_object(self):
        """
        :returns: the PaymentGatewaySession instance or 404 if it doesn't exist.
            It refreshes the data from the related GOV.UK payment record if
            necessary
        """
        obj = super().get_object()
        obj.refresh_from_govuk_payment()
        return obj

    def get_throttles(self):
        """If action is `create`, CreatePaymentGatewaySessionThrottle is used."""
        if self.action == 'create':
            return (CreatePaymentGatewaySessionThrottle(),)
        return ()

    def create(self, request, *args, **kwargs):
        """
        Same as the DRF create but it catches the APIConflictException exception and
        builds a 409 response from it so that DRF does not roll back the transaction
        and therefore losing the potential database changes that we want to keep.

        This is because we have `ATOMIC_REQUESTS` = True and DRF by
        default rolls back the transaction if an exception is raised.
        """
        try:
            return super().create(request, *args, **kwargs)
        except APIConflictException as exc:
            return Response({'detail': exc.detail}, status=exc.status_code)
