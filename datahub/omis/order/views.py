from django.http import Http404

from rest_framework.response import Response
from rest_framework.views import APIView

from datahub.core.viewsets import CoreViewSetV3

from .models import Order, OrderSubscriber
from .serializers import OrderSerializer, SubscribedAdviserSerializer


class OrderViewSet(CoreViewSetV3):
    """Order ViewSet"""

    serializer_class = OrderSerializer
    queryset = Order.objects.select_related(
        'company',
        'contact',
        'primary_market',
    )


class SubscriberListView(APIView):
    """API View for advisers subscribed to an order."""

    def get_order(self, order_pk):
        """
        Returns the order related to the subscriber list or
        raises Http404 if it doesn't exist.
        """
        try:
            return Order.objects.get(pk=order_pk)
        except Order.DoesNotExist:
            raise Http404

    def get_subscriber_list_response(self, order):
        """
        Returns a Response object with the serialised list of advisers subscribed to
        the order.
        """
        advisers = (sub.adviser for sub in order.subscribers.select_related('adviser').all())
        serializer = SubscribedAdviserSerializer(advisers, many=True)

        return Response(serializer.data)

    def get(self, request, order_pk, format=None):
        """
        Returns a serialised list of advisers subscribed to the order.
        """
        order = self.get_order(order_pk)
        return self.get_subscriber_list_response(order)

    def put(self, request, order_pk, format=None):
        """
        Updates a subscriber list.
        It adds/keeps/deletes the advisers based on the new list passed in.
        """
        order = self.get_order(order_pk)

        serializer = SubscribedAdviserSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)

        current_list = set(order.subscribers.values_list('adviser_id', flat=True))
        final_list = {data['id'] for data in serializer.validated_data}

        to_delete = current_list - final_list
        to_add = final_list - current_list

        order.subscribers.filter(adviser__in=to_delete).delete()
        for adviser_id in to_add:
            OrderSubscriber.objects.create(
                order=order,
                adviser_id=adviser_id,
                created_by=self.request.user,
                modified_by=self.request.user
            )

        return self.get_subscriber_list_response(order)
