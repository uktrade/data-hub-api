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
        'investor_type',
        'required_checks_conducted',
        'minimum_return_rate',
        'minimum_equity_percentage',
    ).prefetch_related(
        'deal_ticket_sizes',
        'asset_classes_of_interest',
        'investment_types',
        'time_horizons',
        'restrictions',
        'construction_risks',
        'desired_deal_roles',
        'uk_region_locations',
        'other_countries_being_considered',
    )
