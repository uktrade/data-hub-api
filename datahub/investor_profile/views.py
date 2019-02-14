from oauth2_provider.contrib.rest_framework.permissions import IsAuthenticatedOrTokenHasScope

from datahub.core.viewsets import CoreViewSet
from datahub.investor_profile.constants import ProfileType as ProfileTypeConstant
from datahub.investor_profile.models import InvestorProfile
from datahub.investor_profile.serializers import LargeCapitalInvestorProfileSerializer
from datahub.oauth.scopes import Scope


class LargeCapitalInvestorProfileViewSet(CoreViewSet):
    """Large capital investor profile view set"""

    required_scopes = (Scope.internal_front_end,)
    permission_classes = (IsAuthenticatedOrTokenHasScope,)
    serializer_class = LargeCapitalInvestorProfileSerializer
    profile_type_id = ProfileTypeConstant.large.value.id

    def get_queryset(self):
        """Returns only large capital investor profile queryset"""
        return InvestorProfile.objects.filter(profile_type_id=self.profile_type_id)

    def perform_create(self, serializer):
        """Sets the large capital profile type"""
        serializer.save(profile_type_id=self.profile_type_id)
