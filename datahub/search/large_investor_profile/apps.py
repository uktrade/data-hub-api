from datahub.investment.investor_profile.models import (
    LargeCapitalInvestorProfile as DBLargeCapitalInvestorProfile,
)
from datahub.investment.investor_profile.permissions import InvestorProfilePermission
from datahub.search.apps import SearchApp
from datahub.search.large_investor_profile.models import LargeInvestorProfile


class LargeInvestorProfileSearchApp(SearchApp):
    """SearchApp for large investor profile."""

    name = 'large-investor-profile'
    es_model = LargeInvestorProfile
    view_permissions = (f'investor_profile.{InvestorProfilePermission.view_investor_profile}',)
    export_permission = f'investor_profile.{InvestorProfilePermission.export}'
    exclude_from_global_search = True
    queryset = DBLargeCapitalInvestorProfile.objects.select_related(
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
