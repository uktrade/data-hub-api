from django.http import Http404

from rest_framework import status
from rest_framework.response import Response

from datahub.core.viewsets import CoreViewSetV3
from datahub.oauth.scopes import Scope
from datahub.omis.order.models import Order

from .models import Quote
from .serializers import BasicQuoteSerializer, ExpandedQuoteSerializer, ExpandParamSerializer


class QuoteViewSet(CoreViewSetV3):
    """Quote ViewSet."""

    required_scopes = (Scope.internal_front_end,)
    queryset = Quote.objects.none()
    basic_serializer_class = BasicQuoteSerializer
    expanded_serializer_class = ExpandedQuoteSerializer

    order_lookup_url_kwarg = 'order_pk'

    def preview(self, request, *args, **kwargs):
        """
        Same as `create` but without actually saving the changes.
        """
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

    def get_order(self):
        """
        :returns: the main order from url kwargs.

        :raises Http404: if the order doesn't exist
        """
        try:
            order = Order.objects.get(pk=self.kwargs[self.order_lookup_url_kwarg])
        except Order.DoesNotExist:
            raise Http404('The specified order does not exist.')
        return order

    def get_object(self):
        """
        :returns: the quote related to the order.

        :raises Http404: if the quote doesn't exist
        """
        quote = self.get_order().quote
        if not quote:
            raise Http404('The specified quote does not exist.')
        return quote

    def _requires_expanded(self):
        """
        :returns: True if expanded response required, False otherwise

        This can be implicit from the action or explicitly requested with the
        `expand` query param.
        """
        if self.action in ('create', 'preview'):
            return True

        param_serializer = ExpandParamSerializer(data=self.request.GET)
        param_serializer.is_valid(raise_exception=True)
        return param_serializer.validated_data['expand']

    def get_serializer_class(self):
        """
        :returns: different serializers depending on if the action requires an expanded response
            or the `expand` param has been specified.
        """
        if self._requires_expanded():
            return self.expanded_serializer_class
        return self.basic_serializer_class

    def get_serializer_context(self):
        """Extra context provided to the serializer class."""
        return {
            **super().get_serializer_context(),
            'order': self.get_order(),
            'current_user': self.request.user,
        }
