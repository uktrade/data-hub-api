from datahub.core.viewsets import CoreViewSet
from datahub.feature_flag.utils import feature_flagged_view
from datahub.investment.investor_profile.constants import (
    FEATURE_FLAG_LARGE_CAPITAL_PROFILE,
    ProfileType as ProfileTypeConstant,
)
from datahub.investment.investor_profile.models import InvestorProfile
from datahub.investment.investor_profile.serializers import LargeCapitalInvestorProfileSerializer
from datahub.oauth.scopes import Scope


class LargeCapitalInvestorProfileViewSet(CoreViewSet):
    """Large capital investor profile view set."""

    required_scopes = (Scope.internal_front_end,)
    serializer_class = LargeCapitalInvestorProfileSerializer
    profile_type_id = ProfileTypeConstant.large.value.id

    def get_queryset(self):
        """Returns only large capital investor profile queryset."""
        return InvestorProfile.objects.filter(profile_type_id=self.profile_type_id)

    @feature_flagged_view(FEATURE_FLAG_LARGE_CAPITAL_PROFILE)
    def dispatch(self, request, *args, **kwargs):
        """View dispatch overridden so feature flag can be checked."""
        return super().dispatch(request, *args, **kwargs)
