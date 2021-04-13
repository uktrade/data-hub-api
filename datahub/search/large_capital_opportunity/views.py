from datahub.search.large_capital_opportunity import LargeCapitalOpportunitySearchApp
from datahub.search.large_capital_opportunity.serializers import (
    SearchLargeCapitalOpportunityQuerySerializer,
)
from datahub.search.views import register_v4_view, SearchAPIView


class SearchOpportunityAPIViewMixin:
    """Defines common settings."""

    search_app = LargeCapitalOpportunitySearchApp
    serializer_class = SearchLargeCapitalOpportunityQuerySerializer
    es_sort_by_remappings = {
        'name': 'name.keyword',
    }

    _MAIN_FILTERS = (
        'name',
        'created_by',
        'type',
        'status',
    )

    _DETAIL_FILTERS = (
        'uk_region_location',
        'promoter',
        'promoter_name',
        'lead_dit_relationship_manager',
        'required_checks_conducted',
        'required_checks_conducted_by',
        'asset_class',
        'opportunity_value_start',
        'opportunity_value_end',
        'opportunity_value_type',
        'construction_risk',
    )

    _REQUIREMENT_FILTERS = (
        'total_investment_sought_start',
        'total_investment_sought_end',
        'current_investment_secured_start',
        'current_investment_secured_end',
        'investment_type',
        'estimated_return_rate',
        'time_horizon',
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
        *_EXTRA_FILTERS,
    )

    REMAP_FIELDS = {
        'promoter': 'promoters.id',
        'asset_class': 'asset_classes.id',
        'required_checks_conducted': 'required_checks_conducted.id',
        'required_checks_conducted_by': 'required_checks_conducted_by.id',
        'investment_type': 'investment_types.id',
        'estimated_return_rate': 'estimated_return_rate.id',
        'time_horizon': 'time_horizons.id',
        'construction_risk': 'construction_risks.id',
        'uk_region_location': 'uk_region_locations.id',
        'created_by': 'created_by.id',
        'status': 'status.id',
        'opportunity_value_type': 'opportunity_value_type.id',
        'type': 'type.id',
    }

    COMPOSITE_FILTERS = {
        'name': [
            'name',
            'name.trigram',
        ],
        'promoter_name': [
            'promoters.name',  # to find 2-letter words
            'promoters.name.trigram',
            'promoters.trading_names',  # to find 2-letter words
            'promoters.trading_names.trigram',
        ],
    }


@register_v4_view()
class SearchLargeCapitalOpportunityAPIView(SearchOpportunityAPIViewMixin, SearchAPIView):
    """Filtered large capital opportunity search view."""
