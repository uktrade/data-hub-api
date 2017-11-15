from datahub.investment.permissions import UserTeamInvestmentProjectAssociationCheck, \
    IsTeamAssociatedToInvestmentProjectPermission
from datahub.oauth.scopes import Scope
from .models import InvestmentProject
from .serializers import SearchInvestmentProjectSerializer
from ..views import SearchAPIView, SearchExportAPIView


class SearchInvestmentProjectParams:
    """Search investment project params."""

    required_scopes = (Scope.internal_front_end,)
    entity = InvestmentProject
    serializer_class = SearchInvestmentProjectSerializer

    include_aggregations = True

    FILTER_FIELDS = (
        'client_relationship_manager',
        'estimated_land_date_after',
        'estimated_land_date_before',
        'investment_type',
        'investor_company',
        'investor_company_country',
        'sector',
        'stage',
        'status',
        'uk_region_location',
        'team_members.dit_team.id',
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


class SearchInvestmentProjectAPIView(UserTeamInvestmentProjectAssociationCheck,
                                     SearchInvestmentProjectParams,
                                     SearchAPIView):
    """Filtered investment project search view."""
    permission_classes = SearchAPIView.permission_classes + (IsTeamAssociatedToInvestmentProjectPermission,)
    permission_required = 'investment.read_investmentproject'


class SearchInvestmentProjectExportAPIView(SearchInvestmentProjectParams, SearchExportAPIView):
    """Filtered investment project search export view."""

    permission_required = 'investment.read_investmentproject'
