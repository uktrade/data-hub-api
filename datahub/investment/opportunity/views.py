from django_filters.rest_framework import DjangoFilterBackend

from datahub.core.viewsets import CoreViewSet
from datahub.investment.opportunity.models import LargeCapitalOpportunity
from datahub.investment.opportunity.serializers import LargeCapitalOpportunitySerializer


class LargeCapitalOpportunityViewSet(CoreViewSet):
    """Large capital opportunity view set."""

    serializer_class = LargeCapitalOpportunitySerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('investment_projects__id',)
    queryset = LargeCapitalOpportunity.objects.all()
