from django.http import Http404

from datahub.core.viewsets import CoreViewSetV3

from datahub.omis.order.models import Order

from .models import Quote
from .serializers import QuoteSerializer


class QuoteViewSet(CoreViewSetV3):
    """Quote ViewSet."""

    serializer_class = QuoteSerializer
    queryset = Quote.objects.none()

    order_lookup_url_kwarg = 'order_pk'

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

    def get_serializer_context(self):
        """Extra context provided to the serializer class."""
        return {
            **super().get_serializer_context(),
            'order': self.get_order(),
        }
