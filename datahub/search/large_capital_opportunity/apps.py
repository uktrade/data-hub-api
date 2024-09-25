from datahub.investment.opportunity.models import (
    LargeCapitalOpportunity as DBLargeCapitalOpportunity,
)
from datahub.investment.opportunity.permissions import LargeCapitalOpportunityPermission
from datahub.search.apps import SearchApp
from datahub.search.large_capital_opportunity.models import LargeCapitalOpportunity


class LargeCapitalOpportunitySearchApp(SearchApp):
    """SearchApp for large capital opportunity."""

    name = 'large-capital-opportunity'
    search_model = LargeCapitalOpportunity
    view_permissions = (
        f'opportunity.{LargeCapitalOpportunityPermission.view_large_capital_opportunity}',
    )
    export_permission = f'opportunity.{LargeCapitalOpportunityPermission.export}'
    exclude_from_global_search = True
    queryset = DBLargeCapitalOpportunity.objects.select_related(
        'created_by',
        'created_by__dit_team',
        'lead_dit_relationship_manager',
        'lead_dit_relationship_manager__dit_team',
        'opportunity_value_type',
        'type',
        'status',
        'required_checks_conducted',
        'required_checks_conducted_by',
        'required_checks_conducted_by__dit_team',
        'estimated_return_rate',
    ).prefetch_related(
        'promoters',
        'other_dit_contacts',
        'investment_projects',
        'investment_projects__investmentprojectcode',
        'asset_classes',
        'investment_types',
        'sources_of_funding',
        'time_horizons',
        'construction_risks',
        'uk_region_locations',
        'reasons_for_abandonment',
    )
