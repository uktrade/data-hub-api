from django.http import Http404

from rest_framework.response import Response
from rest_framework.views import APIView

from datahub.core.viewsets import CoreViewSetV3

from .models import Order
from .serializers import OrderAssigneeSerializer, OrderSerializer, SubscribedAdviserSerializer


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

    def get_list_response(self, order):
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
        return self.get_list_response(order)

    def put(self, request, order_pk, format=None):
        """
        Updates a subscriber list.
        It adds/keeps/deletes the advisers based on the new list passed in.
        """
        order = self.get_order(order_pk)

        serializer = SubscribedAdviserSerializer(
            data=request.data,
            many=True,
            context={
                'order': order,
                'modified_by': self.request.user,
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return self.get_list_response(order)


class AssigneeView(APIView):
    """API View for advisers assigned to an order."""

    FORCE_DELETE_PARAM = 'force-delete'

    def get_order(self, order_pk):
        """
        Returns the related order or raises Http404 if it doesn't exist.
        """
        try:
            return Order.objects.get(pk=order_pk)
        except Order.DoesNotExist:
            raise Http404

    def get_list_response(self, order):
        """
        Returns a Response object with the serialised list of advisers assigned to
        the order.
        """
        advisers = order.assignees.select_related('adviser').all()
        serializer = OrderAssigneeSerializer(advisers, many=True)

        return Response(serializer.data)

    def get(self, request, order_pk, format=None):
        """
        Returns a serialised list of advisers assigned to the order.
        """
        order = self.get_order(order_pk)
        return self.get_list_response(order)

    def patch(self, request, order_pk, format=None):
        """
        Updates the list of assignees.
        It adds/keeps/updates/deletes the advisers based on the new list passed in.
        """
        order = self.get_order(order_pk)

        force_delete = request.query_params.get(self.FORCE_DELETE_PARAM, '0').strip() == '1'
        serializer = OrderAssigneeSerializer(
            many=True,
            data=request.data,
            context={
                'order': order,
                'modified_by': self.request.user,
                'force_delete': force_delete
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return self.get_list_response(order)
