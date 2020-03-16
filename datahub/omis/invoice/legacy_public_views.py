from oauth2_provider.contrib.rest_framework.permissions import IsAuthenticatedOrTokenHasScope

from datahub.oauth.scopes import Scope
from datahub.omis.invoice.views import BaseInvoiceViewSet
from datahub.omis.order.constants import OrderStatus
from datahub.omis.order.models import Order


class LegacyPublicInvoiceViewSet(BaseInvoiceViewSet):
    """ViewSet for legacy public facing API."""

    permission_classes = (IsAuthenticatedOrTokenHasScope,)
    required_scopes = (Scope.public_omis_front_end,)

    order_lookup_field = 'public_token'
    order_lookup_url_kwarg = 'public_token'
    order_queryset = Order.objects.publicly_accessible().exclude(
        status=OrderStatus.QUOTE_AWAITING_ACCEPTANCE,
    )
