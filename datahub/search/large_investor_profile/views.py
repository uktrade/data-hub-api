from datahub.oauth.scopes import Scope
from datahub.search.large_investor_profile import LargeInvestorProfileSearchApp
from datahub.search.large_investor_profile.serializers import (
    SearchLargeInvestorProfileQuerySerializer,
)
from datahub.search.views import register_v4_view, SearchAPIView


class SearchInvestorProfileAPIViewMixin:
    """Defines common settings."""

    required_scopes = (Scope.internal_front_end,)
    search_app = LargeInvestorProfileSearchApp
    serializer_class = SearchLargeInvestorProfileQuerySerializer

    _MAIN_FILTERS = (
        'asset_classes_of_interest',
        'country_of_origin',
        'investor_company',
        'investor_company_name',
        'created_by',
    )

    _DETAIL_FILTERS = (
        'investor_type',
        'investable_capital_start',
        'investable_capital_end',
        'global_assets_under_management_start',
        'global_assets_under_management_end',
        'required_checks_conducted',
    )

    _REQUIREMENT_FILTERS = (
        'deal_ticket_size',
        'investment_type',
        'minimum_return_rate',
        'time_horizon',
        'restriction',
        'construction_risk',
        'minimum_equity_percentage',
        'desired_deal_role',
    )

    _LOCATION_FILTERS = (
        'uk_region_location',
        'other_countries_being_considered',
    )

    _EXTRA_FILTERS = (
        'created_on_before',
        'created_on_after',
    )

    FILTER_FIELDS = (
        'id',
        *_MAIN_FILTERS,
        *_DETAIL_FILTERS,
        *_REQUIREMENT_FILTERS,
        *_LOCATION_FILTERS,
        *_EXTRA_FILTERS,
    )

    REMAP_FIELDS = {
        'investor_company': 'investor_company.id',
        'country_of_origin': 'country_of_origin.id',
        'asset_classes_of_interest': 'asset_classes_of_interest.id',
        'investor_type': 'investor_type.id',
        'required_checks_conducted': 'required_checks_conducted.id',
        'deal_ticket_size': 'deal_ticket_sizes.id',
        'investment_type': 'investment_types.id',
        'minimum_return_rate': 'minimum_return_rate.id',
        'time_horizon': 'time_horizons.id',
        'restriction': 'restrictions.id',
        'construction_risk': 'construction_risks.id',
        'minimum_equity_percentage': 'minimum_equity_percentage.id',
        'desired_deal_role': 'desired_deal_roles.id',
        'uk_region_location': 'uk_region_locations.id',
        'other_countries_being_considered': 'other_countries_being_considered.id',
        'created_by': 'created_by.id',
    }

    COMPOSITE_FILTERS = {
        'investor_company_name': [
            'investor_company.name',  # to find 2-letter words
            'investor_company.name.trigram',
            'investor_company.trading_names',  # to find 2-letter words
            'investor_company.trading_names.trigram',
        ],
    }


@register_v4_view()
class SearchLargeInvestorProfileAPIView(SearchInvestorProfileAPIViewMixin, SearchAPIView):
    """Filtered large capital investor profile search view."""

    es_sort_by_remappings = {
        'investor_company.name': 'investor_company.name.keyword',
    }
