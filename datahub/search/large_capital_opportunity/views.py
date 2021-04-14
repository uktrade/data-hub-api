from datahub.core.query_utils import (
    get_front_end_url_expression,
    get_full_name_expression,
    get_string_agg_subquery,
)
from datahub.investment.opportunity.models import (
    LargeCapitalOpportunity as DBLargeCapitalOpportunity,
)
from datahub.search.large_capital_opportunity import LargeCapitalOpportunitySearchApp
from datahub.search.large_capital_opportunity.serializers import (
    SearchLargeCapitalOpportunityQuerySerializer,
)
from datahub.search.views import register_v4_view, SearchAPIView, SearchExportAPIView


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


@register_v4_view(sub_path='export')
class SearchLargeCapitalOpportunityExportAPIView(
    SearchOpportunityAPIViewMixin,
    SearchExportAPIView,
):
    """Large capital opportunity search export view."""

    queryset = DBLargeCapitalOpportunity.objects.annotate(
        required_checks_conducted_by_name=get_full_name_expression(
            'required_checks_conducted_by',
        ),
        lead_dit_relationship_manager_name=get_full_name_expression(
            'lead_dit_relationship_manager',
        ),
        created_by_name=get_full_name_expression('created_by'),
        asset_class_names=get_string_agg_subquery(
            DBLargeCapitalOpportunity,
            'asset_classes__name',
        ),
        type_names=get_string_agg_subquery(
            DBLargeCapitalOpportunity,
            'type__name',
        ),
        status_names=get_string_agg_subquery(
            DBLargeCapitalOpportunity,
            'status__name',
        ),
        promoter_names=get_string_agg_subquery(
            DBLargeCapitalOpportunity,
            'promoters__name',
        ),
        other_dit_contact_names=get_string_agg_subquery(
            DBLargeCapitalOpportunity,
            get_full_name_expression('other_dit_contacts'),
            ordering=('other_dit_contacts__first_name', 'other_dit_contacts__last_name'),
        ),
        investment_type_names=get_string_agg_subquery(
            DBLargeCapitalOpportunity,
            'investment_types__name',
        ),
        time_horizons_names=get_string_agg_subquery(
            DBLargeCapitalOpportunity,
            'time_horizons__name',
        ),
        sources_of_funding_names=get_string_agg_subquery(
            DBLargeCapitalOpportunity,
            'sources_of_funding__name',
        ),
        construction_risks_names=get_string_agg_subquery(
            DBLargeCapitalOpportunity,
            'construction_risks__name',
        ),
        uk_region_locations_names=get_string_agg_subquery(
            DBLargeCapitalOpportunity,
            'uk_region_locations__name',
        ),
        reasons_for_abandonment_names=get_string_agg_subquery(
            DBLargeCapitalOpportunity,
            'reasons_for_abandonment__name',
        ),
        link=get_front_end_url_expression(
            'largecapitalopportunity',
            'id',
            url_suffix='/investments/large-capital-opportunity',
        ),
    )

    field_titles = {
        'created_on': 'Date created',
        'created_by_name': 'Created by',
        'id': 'Data Hub opportunity reference',
        'link': 'Data Hub link',
        'name': 'Name',
        'description': 'Description',
        'type__name': 'Type',
        'status__name': 'Status',
        'uk_region_locations_names': 'UK region locations',
        'promoter_names': 'Promoters',
        'lead_dit_relationship_manager_name': 'Lead DIT relationship manager',
        'other_dit_contact_names': 'Other DIT contacts',
        'required_checks_conducted__name': 'Required checks conducted',
        'required_checks_conducted_by_name': 'Required checks conducted by',
        'required_checks_conducted_on': 'Required checks conducted on',
        'asset_class_names': 'Asset classes',
        'opportunity_value_type__name': 'Opportunity value type',
        'opportunity_value': 'Opportunity value',
        'construction_risks_names': 'Construction risks',
        'total_investment_sought': 'Total investment sought',
        'current_investment_secured': 'Current investment secured',
        'investment_type_names': 'Investment types',
        'estimated_return_rate__name': 'Estimated return rate',
        'time_horizons_names': 'Time horizons',
        'sources_of_funding_names': 'Sources of funding',
        'dit_support_provided': 'DIT support provided',
        'funding_supporting_details': 'Funding supporting details',
        'reasons_for_abandonment_names': 'Reasons for abandonment',
        'why_abandoned': 'Why abandoned',
        'why_suspended': 'Why suspended',
        'modified_on': 'Date last modified',
    }
