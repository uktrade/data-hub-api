from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from datahub.company.models import Company
from datahub.company_activity.serializers import (
    CompanyActivityFilterSerializer,
    CompanyActivitySerializer,
)
from datahub.core.viewsets import CoreViewSet


class CompanyActivityViewSetV4(CoreViewSet):
    """Company Activity ViewSet v4."""

    filter_backends = (DjangoFilterBackend, OrderingFilter)
    http_method_names = ['post']
    serializer_class = CompanyActivitySerializer
    queryset = Company.objects.prefetch_related(
        'interactions',
        'interactions__contacts',
        'interactions__service',
        'interactions__dit_participants__adviser',
        'interactions__dit_participants__team',
        'interactions__communication_channel',
    )

    def retrieve(self, request, *args, **kwargs):
        if request.data:
            CompanyActivityFilterSerializer(data=request.data).is_valid(
                raise_exception=True,
            )
        return super().retrieve(request, *args, **kwargs)
