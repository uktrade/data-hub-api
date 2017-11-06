from django.http import Http404
from oauth2_provider.contrib.rest_framework.permissions import IsAuthenticatedOrTokenHasScope

from datahub.oauth.scopes import Scope
from datahub.omis.order.constants import OrderStatus
from datahub.omis.order.models import Order
from datahub.omis.order.views import BaseNestedOrderViewSet
from datahub.permissions import CrudPermission

from .models import Invoice
from .serializers import InvoiceSerializer


class BaseInvoiceViewSet(BaseNestedOrderViewSet):
    """Base Invoice ViewSet."""

    queryset = Invoice.objects.none()
    serializer_class = InvoiceSerializer

    def get_object(self):
        """
        :returns: the invoice related to the order.

        :raises Http404: if the invoice doesn't exist
        """
        invoice = self.get_order().invoice
        if not invoice:
            raise Http404('The specified invoice does not exist.')
        return invoice


class InvoiceViewSet(BaseInvoiceViewSet):
    """Invoice ViewSet."""

    required_scopes = (Scope.internal_front_end,)


class PublicInvoiceViewSet(BaseInvoiceViewSet):
    """ViewSet for public facing API."""

    required_scopes = (Scope.public_omis_front_end,)

    order_lookup_field = 'public_token'
    order_lookup_url_kwarg = 'public_token'
    order_queryset = Order.objects.publicly_accessible().exclude(
        status=OrderStatus.quote_awaiting_acceptance
    )
