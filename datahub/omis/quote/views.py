from django.http import Http404
from rest_framework import status
from rest_framework.response import Response

from config.settings.types import HawkScope
from datahub.core.auth import PaaSIPAuthentication
from datahub.core.hawk_receiver import (
    HawkAuthentication,
    HawkResponseSigningMixin,
    HawkScopePermission,
)
from datahub.omis.order.models import Order
from datahub.omis.order.views import BaseNestedOrderViewSet
from datahub.omis.quote.models import Quote
from datahub.omis.quote.serializers import PublicQuoteSerializer, QuoteSerializer


class BaseQuoteViewSet(BaseNestedOrderViewSet):
    """Base Quote ViewSet."""

    queryset = Quote.objects.none()

    def get_object(self):
        """:returns: the quote related to the order.

        :raises Http404: if the quote doesn't exist
        """
        quote = self.get_order_or_404().quote
        if not quote:
            raise Http404('The specified quote does not exist.')
        return quote


class QuoteViewSet(BaseQuoteViewSet):
    """Quote ViewSet."""

    serializer_class = QuoteSerializer

    def preview(self, request, *args, **kwargs):
        """Same as `create` but without actually saving the changes."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.preview()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def cancel(self, request, *args, **kwargs):
        """Cancel a quote."""
        self.get_object()  # check if quote exists

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.cancel()

        return Response(serializer.data, status=status.HTTP_200_OK)


class PublicQuoteViewSet(HawkResponseSigningMixin, BaseQuoteViewSet):
    """ViewSet for Hawk authenticated public facing API."""

    authentication_classes = (PaaSIPAuthentication, HawkAuthentication)
    permission_classes = (HawkScopePermission,)
    required_hawk_scope = HawkScope.public_omis
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
