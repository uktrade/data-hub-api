from django.http import Http404

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from datahub.core.viewsets import CoreViewSetV3
from datahub.oauth.scopes import Scope

from .models import Order
from .serializers import (
    CancelOrderSerializer,
    CompleteOrderSerializer,
    OrderAssigneeSerializer,
    OrderSerializer,
    PublicOrderSerializer,
    SubscribedAdviserSerializer
)


class OrderViewSet(CoreViewSetV3):
    """Order ViewSet"""

    required_scopes = (Scope.internal_front_end,)
    serializer_class = OrderSerializer
    queryset = Order.objects.select_related(
        'company',
        'contact',
        'primary_market',
    )

    def complete(self, request, *args, **kwargs):
        """Complete an order."""
        instance = self.get_object()
        serializer = CompleteOrderSerializer(
            instance,
            data={},
            context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.complete()
        return Response(
            self.get_serializer(instance=instance).data,
            status=status.HTTP_200_OK
        )

    def cancel(self, request, *args, **kwargs):
        """Cancel an order."""
        instance = self.get_object()
        serializer = CancelOrderSerializer(
            instance,
            data=request.data,
            context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.cancel()
        return Response(
            self.get_serializer(instance=instance).data,
            status=status.HTTP_200_OK
        )

    def get_serializer_context(self):
        """Extra context provided to the serializer class."""
        return {
            **super().get_serializer_context(),
            'current_user': self.request.user,
        }


class PublicOrderViewSet(CoreViewSetV3):
    """ViewSet for public facing order endpoint."""

    lookup_field = 'public_token'

    required_scopes = (Scope.public_omis_front_end,)
    serializer_class = PublicOrderSerializer
    queryset = Order.objects.publicly_accessible(
        include_reopened=True
    ).select_related(
        'company',
        'contact'
    )


class SubscriberListView(APIView):
    """API View for advisers subscribed to an order."""

    required_scopes = (Scope.internal_front_end,)

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
    required_scopes = (Scope.internal_front_end,)

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


class BaseNestedOrderViewSet(CoreViewSetV3):
    """
    Base class for nested viewsets with order as parent
    E.g. /order/<order-id>/<child>
    """

    serializer_class = None

    order_lookup_field = 'pk'
    order_lookup_url_kwarg = 'order_pk'
    order_queryset = Order.objects

    def get_order(self):
        """
        :returns: the main order from url kwargs.

        :raises Http404: if the order doesn't exist
        """
        try:
            order = self.order_queryset.get(
                **{self.order_lookup_field: self.kwargs[self.order_lookup_url_kwarg]}
            )
        except Order.DoesNotExist:
            raise Http404('The specified order does not exist.')
        return order

    def get_serializer_context(self):
        """Extra context provided to the serializer class."""
        return {
            **super().get_serializer_context(),
            'order': self.get_order(),
            'current_user': self.request.user,
        }
