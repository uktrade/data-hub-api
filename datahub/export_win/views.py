from datetime import datetime

from django.conf import settings
from django.db.models import Max, Min

from django.http import Http404
from django_filters.rest_framework import (
    DjangoFilterBackend,
    Filter,
    FilterSet,
)

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.views import Response

from datahub.core.schemas import StubSchema

from datahub.core.viewsets import CoreViewSet
from datahub.export_win.models import (
    CustomerResponse,
    CustomerResponseToken,
    Win,
)
from datahub.export_win.serializers import (
    PublicCustomerResponseSerializer,
    WinSerializer,
)
from datahub.export_win.tasks import (
    create_token_for_contact,
    get_all_fields_for_client_email_receipt,
    notify_export_win_email_by_rq_email,
    update_customer_response_token_for_email_notification_id,
)


class NullBooleanFieldFilter(Filter):
    """Null boolean field filter."""

    def filter(self, qs, value):
        """Filter query"""
        if value is not None:
            sanitised_value = value.strip().lower()
            if sanitised_value == 'null':
                return qs.filter(
                    **{f'{self.field_name}__isnull': True},
                )
            elif sanitised_value == 'true':
                return qs.filter(
                    **{self.field_name: True},
                )
            elif sanitised_value == 'false':
                return qs.filter(
                    **{self.field_name: False},
                )
        return qs


class ConfirmedFilterSet(FilterSet):
    """Filter set for confirmed, unconfirmed, unanswered wins."""

    confirmed = NullBooleanFieldFilter(
        field_name='customer_response__agree_with_win',
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
        'customer_response',
    ).prefetch_related(
        'type_of_support',
        'associated_programme',
        'team_members',
        'advisers',
    ).annotate(
        first_sent=Min('customer_response__tokens__created_on'),
        last_sent=Max('customer_response__tokens__created_on'),
    )
    filter_backends = [DjangoFilterBackend]
    filterset_class = ConfirmedFilterSet

    def perform_create(self, serializer):
        """
        Ensure instance with first sent and last sent dates
        is available to serializer.
        """
        instance = serializer.save()
        serializer.instance = self.get_queryset().get(pk=instance.pk)

    @action(methods=['post'], detail=True, schema=StubSchema())
    def resend_export_win(self, request, *args, **kwargs):
        """
        Resend email manually via ITA dashboard
        """
        win = self.get_object()
        contact = win.company_contacts.first()
        customer_response = win.customer_response
        new_token = create_token_for_contact(contact, customer_response)
        context = get_all_fields_for_client_email_receipt(
            new_token,
            customer_response,
        )
        template_id = settings.EXPORT_WIN_CLIENT_RECEIPT_TEMPLATE_ID
        notify_export_win_email_by_rq_email(
            contact.email,
            template_id,
            context,
            update_customer_response_token_for_email_notification_id,
            new_token.id,
        )
        data = {
            'message': 'Email has successfully been re-sent',
        }
        return Response(data, status=status.HTTP_200_OK)


class CustomerResponseViewSet(CoreViewSet):
    """Views for Customer response."""

    # this endpoint is publicly accessible
    authentication_classes = ()
    permission_classes = (AllowAny,)
    serializer_class = PublicCustomerResponseSerializer
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
            self.token = token
            return self.queryset.get(
                id=token.customer_response_id,
            )
        except CustomerResponseToken.DoesNotExist:
            raise Http404

    def get_serializer_context(self):
        """Add token_pk to serializer context."""
        context = super().get_serializer_context()
        context['token_pk'] = self.kwargs.get('token_pk')
        context['token'] = getattr(self, 'token', None)
        return context

    def put(self, request, *args, **kwargs):
        return Response(status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, *args, **kwargs):
        return Response(status=status.HTTP_404_NOT_FOUND)
