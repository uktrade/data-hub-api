from django_filters.rest_framework import DjangoFilterBackend, FilterSet

from datahub.core.audit import AuditViewSet
from datahub.core.autocomplete import AutocompleteFilter
from datahub.core.viewsets import CoreViewSet
from datahub.investment.opportunity.models import LargeCapitalOpportunity
from datahub.investment.opportunity.serializers import LargeCapitalOpportunitySerializer


class LargeCapitalOpportunityFilterSet(FilterSet):
    """Large Capital Opportunity filter."""

    autocomplete = AutocompleteFilter(search_fields=('name',))

    class Meta:
        model = LargeCapitalOpportunity
        fields = ['investment_projects__id']


class LargeCapitalOpportunityViewSet(CoreViewSet):
    """Large capital opportunity view set."""

    serializer_class = LargeCapitalOpportunitySerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = LargeCapitalOpportunityFilterSet
    queryset = LargeCapitalOpportunity.objects.all()


class LargeCapitalOpportunityAuditViewSet(AuditViewSet):
    """Large capital opportunity audit views."""

    queryset = LargeCapitalOpportunity.objects.all()
