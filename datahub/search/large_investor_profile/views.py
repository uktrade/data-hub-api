from django.db.models import CharField
from django.db.models.functions import Cast

from datahub.core.query_utils import (
    get_front_end_url_expression,
    get_full_name_expression,
    get_string_agg_subquery,
)
from datahub.investment.investor_profile.models import (
    LargeCapitalInvestorProfile as DBLargeCapitalInvestorProfile,
)
from datahub.search.large_investor_profile import LargeInvestorProfileSearchApp
from datahub.search.large_investor_profile.serializers import (
    SearchLargeInvestorProfileQuerySerializer,
)
from datahub.search.views import SearchAPIView, SearchExportAPIView, register_v4_view


class SearchInvestorProfileAPIViewMixin:
    """Defines common settings."""

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

    es_sort_by_remappings = {
        'investor_company.name': 'investor_company.name.keyword',
    }


@register_v4_view()
class SearchLargeInvestorProfileAPIView(SearchInvestorProfileAPIViewMixin, SearchAPIView):
    """Filtered large capital investor profile search view."""


@register_v4_view(sub_path='export')
class SearchLargeInvestorProfileExportAPIView(
    SearchInvestorProfileAPIViewMixin,
    SearchExportAPIView,
):
    """Large capital investor profile search export view."""

    queryset = DBLargeCapitalInvestorProfile.objects.annotate(
        required_checks_conducted_by_name=get_full_name_expression(
            'required_checks_conducted_by',
        ),
        deal_ticket_sizes_names=get_string_agg_subquery(
            DBLargeCapitalInvestorProfile,
            Cast('deal_ticket_sizes__name', CharField()),
        ),
        asset_classes_of_interest_names=get_string_agg_subquery(
            DBLargeCapitalInvestorProfile,
            Cast('asset_classes_of_interest__name', CharField()),
        ),
        investment_types_names=get_string_agg_subquery(
            DBLargeCapitalInvestorProfile,
            Cast('investment_types__name', CharField()),
        ),
        time_horizons_names=get_string_agg_subquery(
            DBLargeCapitalInvestorProfile,
            Cast('time_horizons__name', CharField()),
        ),
        restrictions_names=get_string_agg_subquery(
            DBLargeCapitalInvestorProfile,
            Cast('restrictions__name', CharField()),
        ),
        construction_risks_names=get_string_agg_subquery(
            DBLargeCapitalInvestorProfile,
            Cast('construction_risks__name', CharField()),
        ),
        desired_deal_roles_names=get_string_agg_subquery(
            DBLargeCapitalInvestorProfile,
            Cast('desired_deal_roles__name', CharField()),
        ),
        uk_region_locations_names=get_string_agg_subquery(
            DBLargeCapitalInvestorProfile,
            Cast('uk_region_locations__name', CharField()),
        ),
        other_countries_being_considered_names=get_string_agg_subquery(
            DBLargeCapitalInvestorProfile,
            Cast('other_countries_being_considered__name', CharField()),
        ),
        link=get_front_end_url_expression(
            'company',
            'investor_company_id',
            url_suffix='/investments/large-capital-profile',
        ),
    )

    field_titles = {
        'created_on': 'Date created',
        'id': 'Data Hub profile reference',
        'link': 'Data Hub link',
        'investor_company__name': 'Investor company',
        'investor_type__name': 'Investor type',
        'investable_capital': 'Investable capital',
        'global_assets_under_management': 'Global assets under management',
        'investor_description': 'Investor description',
        'required_checks_conducted__name': 'Required checks conducted',
        'required_checks_conducted_by_name': 'Required checks conducted by',
        'required_checks_conducted_on': 'Required checks conducted on',
        'deal_ticket_sizes_names': 'Deal ticket sizes',
        'asset_classes_of_interest_names': 'Asset classes of interest',
        'investment_types_names': 'Investment types',
        'minimum_return_rate__name': 'Minimum return rate',
        'time_horizons_names': 'Time horizons',
        'restrictions_names': 'Restrictions',
        'construction_risks_names': 'Construction risks',
        'minimum_equity_percentage__name': 'Minimum equity percentage',
        'desired_deal_roles_names': 'Desired deal roles',
        'uk_region_locations_names': 'UK regions of interest',
        'other_countries_being_considered_names': 'Other countries being considered',
        'notes_on_locations': 'Notes on locations',
        'modified_on': 'Date last modified',
    }
