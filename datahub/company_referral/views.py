from django.db.models import Q

from datahub.company_referral.models import CompanyReferral
from datahub.company_referral.serializers import CompanyReferralSerializer
from datahub.core.viewsets import CoreViewSet
from datahub.oauth.scopes import Scope


class CompanyReferralViewSet(CoreViewSet):
    """Company referral view set."""

    serializer_class = CompanyReferralSerializer
    required_scopes = (Scope.internal_front_end,)
    queryset = CompanyReferral.objects.select_related(
        'company',
        'contact',
        'created_by__dit_team',
        'recipient__dit_team',
    )

    def get_queryset(self):
        """
        Get a queryset for list action that is filtered to the authenticated user's sent and
        received referrals, otherwise return original queryset.
        """
        if self.action == 'list':
            return super().get_queryset().filter(
                Q(created_by=self.request.user) | Q(recipient=self.request.user),
            )

        return super().get_queryset()
