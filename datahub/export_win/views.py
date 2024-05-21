import functools
import logging

from datetime import datetime

from django.conf import settings
from django.db.models import Max, Min, Q

from django.http import Http404
from django_filters.rest_framework import (
    DjangoFilterBackend,
    Filter,
    FilterSet,
)

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import AllowAny
from rest_framework.views import exception_handler, Response

from datahub.core.schemas import StubSchema

from datahub.core.viewsets import CoreViewSet
from datahub.export_win import EXPORT_WINS_LEGACY_DATA_FEATURE_FLAG_NAME
from datahub.export_win.decorators import validate_script_and_html_tags
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
from datahub.feature_flag.utils import (
    is_user_feature_flag_active,
)

logger = logging.getLogger(__name__)


def log_bad_request(view_method):
    @functools.wraps(view_method)
    def wrapper(self, request, *args, **kwargs):
        try:
            return view_method(self, request, *args, **kwargs)
        except Exception as e:
            if getattr(e, 'status_code', None) == status.HTTP_400_BAD_REQUEST:
                response = exception_handler(e, context={'request': request})
                logger.error(
                    'Export Wins API Bad Request',
                    extra={
                        'request_data': request.data,
                        'response_data': response.data,
                    },
                )
            raise
    return wrapper


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
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = ConfirmedFilterSet
    ordering_fields = ('customer_response__responded_on', 'created_on')
    ordering = ('-customer_response__responded_on', '-created_on')

    def get_queryset(self):
        """Filter the queryset to the authenticated user."""
        if is_user_feature_flag_active(
            EXPORT_WINS_LEGACY_DATA_FEATURE_FLAG_NAME,
            self.request.user,
        ):
            migrated_filter = {}
        else:
            migrated_filter = {
                'migrated_on__isnull': True,
            }
        return (
            super()
            .get_queryset()
            .filter(
                **migrated_filter,
            )
            .exclude(
                ~Q(adviser=self.request.user),
                ~Q(team_members=self.request.user),
                ~Q(lead_officer=self.request.user),
                ~(
                    Q(advisers__adviser=self.request.user)
                    & Q(customer_response__agree_with_win=True)
                ),
            )
        )

    @log_bad_request
    @validate_script_and_html_tags
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @log_bad_request
    @validate_script_and_html_tags
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

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
        if customer_response.agree_with_win is not None:
            # Customer already responded to win
            raise Http404
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

    @validate_script_and_html_tags
    def partial_update(self, request, *args, **kwargs):
        """Handle PATCH requests with HTML/script tags validation."""
        return super().partial_update(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return Response(status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, *args, **kwargs):
        return Response(status=status.HTTP_404_NOT_FOUND)
