from datetime import datetime

from django.http import Http404

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import Response

from datahub.core.viewsets import CoreViewSet
from datahub.export_win.models import (
    CustomerResponse,
    CustomerResponseToken,
    Win,
)
from datahub.export_win.serializers import (
    CustomerResponseSerializer,
    WinSerializer,
)


class WinViewSet(CoreViewSet):
    """Views for Export wins."""

    serializer_class = WinSerializer
    queryset = Win.objects.select_related(
        'customer_location',
        'type',
        'country',
        'goods_vs_services',
        'sector',
        'hvc',
        'hvo_programme',
        'lead_officer',
        'line_manager',
        'team_type',
        'hq_team',
        'business_potential',
        'export_experience',
    ).prefetch_related(
        'type_of_support',
        'associated_programme',
        'team_members',
        'advisers',
    )


class CustomerResponseViewSet(CoreViewSet):
    """Views for Customer response."""

    permission_classes = (AllowAny,)
    serializer_class = CustomerResponseSerializer
    queryset = CustomerResponse.objects.all()
    lookup_field = 'token_pk'
    lookup_url_kwarg = 'token_pk'

    def get_object(self):
        token_pk = self.kwargs.get('token_pk')
        try:
            now = datetime.utcnow()
            token = CustomerResponseToken.objects.get(
                pk=token_pk,
                expires_on__gt=now,
            )
            token.times_used += 1
            token.save()
            return self.queryset.get(
                id=token.customer_response_id,
            )
        except CustomerResponseToken.DoesNotExist:
            raise Http404

    def get_serializer_context(self):
        """Add token_pk to serializer context."""
        context = super().get_serializer_context()
        context['token_pk'] = self.kwargs.get('token_pk')
        return context

    def put(self, request, *args, **kwargs):
        return Response(status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, *args, **kwargs):
        return Response(status=status.HTTP_404_NOT_FOUND)
