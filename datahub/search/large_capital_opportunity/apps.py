from datahub.investment.opportunity.models import (
    LargeCapitalOpportunity as DBLargeCapitalOpportunity,
)
from datahub.investment.opportunity.permissions import LargeCapitalOpportunityPermission
from datahub.search.apps import SearchApp
from datahub.search.large_capital_opportunity.models import LargeCapitalOpportunity


class LargeCapitalOpportunitySearchApp(SearchApp):
    """SearchApp for large capital opportunity."""

    name = 'large-capital-opportunity'
    es_model = LargeCapitalOpportunity
    view_permissions = (
        f'opportunity.{LargeCapitalOpportunityPermission.view_large_capital_opportunity}',
    )
    export_permission = f'opportunity.{LargeCapitalOpportunityPermission.export}'
    exclude_from_global_search = True
    queryset = DBLargeCapitalOpportunity.objects.select_related(
        'lead_dit_relationship_manager',
        'type',
        'status',
        'required_checks_conducted',
        'required_checks_conducted_by',
        'estimated_return_rate',
    ).prefetch_related(
        'promoters',
        'other_dit_contacts',
        'investment_projects',
        'asset_classes',
        'investment_types',
        'sources_of_funding',
        'time_horizons',
        'construction_risks',
        'uk_region_locations',
    )
