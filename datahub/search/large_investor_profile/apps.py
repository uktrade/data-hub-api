from datahub.investment.investor_profile.constants import ProfileType
from datahub.investment.investor_profile.models import InvestorProfile as DBInvestorProfile
from datahub.investment.investor_profile.permissions import InvestorProfilePermission
from datahub.search.apps import SearchApp
from datahub.search.large_investor_profile.models import (
    DOC_TYPE as LARGE_INVESTOR_PROFILE_DOC_TYPE,
    LargeInvestorProfile,
)


class LargeInvestorProfileSearchApp(SearchApp):
    """SearchApp for investor profile."""

    name = LARGE_INVESTOR_PROFILE_DOC_TYPE
    es_model = LargeInvestorProfile
    view_permissions = (f'investor_profile.{InvestorProfilePermission.view_investor_profile}',)
    queryset = DBInvestorProfile.objects.filter(
        profile_type_id=ProfileType.large.value.id,
    ).select_related(
        'investor_company',
    )
