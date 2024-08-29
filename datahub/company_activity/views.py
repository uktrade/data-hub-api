from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from datahub.company.models import Company
from datahub.company_activity.serializers import CompanyActivitySerializer
from datahub.core.viewsets import CoreViewSet


class CompanyActivityViewSetV4(CoreViewSet):
    """Company Activity ViewSet v4."""

    filter_backends = (DjangoFilterBackend, OrderingFilter)
    http_method_names = ['post',]
    serializer_class = CompanyActivitySerializer
    queryset = Company.objects.prefetch_related(
        'company_interactions',
        'company_interactions__contacts',
        'company_interactions__service',
        'company_interactions__dit_participants__adviser',
        'company_interactions__dit_participants__team',
        'company_interactions__communication_channel',
    )
