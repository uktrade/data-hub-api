from datahub.oauth.scopes import Scope
from .models import InvestmentProject
from .serializers import SearchInvestmentProjectSerializer
from ..views import SearchAPIView


class SearchInvestmentProjectParams:
    """Search investment project params."""

    required_scopes = (Scope.internal_front_end,)
    entity = InvestmentProject
    serializer_class = SearchInvestmentProjectSerializer

    include_aggregations = True

    FILTER_FIELDS = (
        'adviser',
        'client_relationship_manager',
        'created_on_after',
        'created_on_before',
        'estimated_land_date_after',
        'estimated_land_date_before',
        'actual_land_date_after',
        'actual_land_date_before',
        'investment_type',
        'investor_company',
        'investor_company_country',
        'sector',
        'sector_descends',
        'stage',
        'status',
        'uk_region_location',
    )

    REMAP_FIELDS = {
        'client_relationship_manager': 'client_relationship_manager.id',
        'investment_type': 'investment_type.id',
        'investor_company': 'investor_company.id',
        'investor_company_country': 'investor_company_country.id',
        'sector': 'sector.id',
        'stage': 'stage.id',
        'uk_region_location': 'uk_region_locations.id',
    }

    COMPOSITE_FILTERS = {
        'adviser': [
            'created_by.id',
            'client_relationship_manager.id',
            'project_assurance_adviser.id',
            'project_manager.id',
            'team_members.id',
        ],
        'sector_descends': [
            'sector.id',
            'sector.ancestors.id'
        ],
    }


class SearchInvestmentProjectAPIView(SearchInvestmentProjectParams, SearchAPIView):
    """Filtered investment project search view."""
