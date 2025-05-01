from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from rest_framework.generics import RetrieveAPIView
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from datahub.company_activity.filters import KingsAwardRecipientFilterSet
from datahub.company_activity.models import KingsAwardRecipient, StovaEvent
from datahub.company_activity.serializers.kings_award import KingsAwardRecipientSerializer
from datahub.company_activity.serializers.stova import StovaEventSerializer


class StovaEventRetrieveAPIView(RetrieveAPIView):
    queryset = StovaEvent.objects.all()
    serializer_class = StovaEventSerializer


class KingsAwardRecipientViewSet(
    ListModelMixin,
    RetrieveModelMixin,
    GenericViewSet,
):
    """ViewSet for listing and filtering King's Award Recipients. The following
    csv-filters are available: `year_awarded`, `category` (via alias in model).
    """

    serializer_class = KingsAwardRecipientSerializer
    queryset = KingsAwardRecipient.objects.select_related('company').all()
    permission_classes = (IsAuthenticated,)
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = KingsAwardRecipientFilterSet
    ordering_fields = ('year_awarded', 'company__name')
    ordering = ('-year_awarded', 'company__name')
