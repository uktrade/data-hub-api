from oauth2_provider.contrib.rest_framework.permissions import IsAuthenticatedOrTokenHasScope
from rest_framework import status
from rest_framework.response import Response

from datahub.oauth.scopes import Scope
from datahub.omis.order.models import Order
from datahub.omis.quote.serializers import PublicQuoteSerializer
from datahub.omis.quote.views import BaseQuoteViewSet


class LegacyPublicQuoteViewSet(BaseQuoteViewSet):
    """ViewSet for legacy public facing API."""

    permission_classes = (IsAuthenticatedOrTokenHasScope,)
    required_scopes = (Scope.public_omis_front_end,)
    serializer_class = PublicQuoteSerializer

    order_lookup_field = 'public_token'
    order_lookup_url_kwarg = 'public_token'
    order_queryset = Order.objects.publicly_accessible(include_reopened=True)

    def accept(self, request, *args, **kwargs):
        """Accept a quote."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.accept()
        return Response(serializer.data, status=status.HTTP_200_OK)
