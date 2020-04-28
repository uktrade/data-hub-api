from django_filters.rest_framework import DjangoFilterBackend

from datahub.core.viewsets import CoreViewSet
from datahub.investment.investor_profile.models import LargeCapitalInvestorProfile
from datahub.investment.investor_profile.serializers import LargeCapitalInvestorProfileSerializer


class LargeCapitalInvestorProfileViewSet(CoreViewSet):
    """Large capital investor profile view set."""

    serializer_class = LargeCapitalInvestorProfileSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('investor_company_id',)
    queryset = LargeCapitalInvestorProfile.objects.all()
