from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope

from datahub.investment.models import InvestmentProject as DBInvestmentProject
from datahub.investment.permissions import (
    InvestmentProjectAssociationChecker, InvestmentProjectModelPermissions,
    IsAssociatedToInvestmentProjectPermission, Permissions
)
from datahub.oauth.scopes import Scope
from .models import InvestmentProject
from .serializers import SearchInvestmentProjectSerializer
from ..views import SearchAPIView, SearchExportAPIView


class SearchInvestmentProjectParams:
    """Search investment project params."""

    permission_classes = (
        IsAuthenticatedOrTokenHasScope,
        InvestmentProjectModelPermissions,
        IsAssociatedToInvestmentProjectPermission
    )
    permission_required = f'investment.{Permissions.read_all}'
    required_scopes = (Scope.internal_front_end,)
    entity = InvestmentProject
    model = DBInvestmentProject
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

    def get_permission_filter_args(self):
        """Gets permission filter arguments."""
        checker = InvestmentProjectAssociationChecker()

        if not checker.should_apply_restrictions(self.request, self):
            return None

        dit_team_id = str(self.request.user.dit_team_id) if self.request.user else None
        filters = {
            f'{field}.dit_team.id': dit_team_id
            for field in DBInvestmentProject.ASSOCIATED_ADVISER_TO_ONE_FIELDS
        }

        filters.update({
            f'{field.es_field_name}.dit_team.id': dit_team_id
            for field in DBInvestmentProject.ASSOCIATED_ADVISER_TO_MANY_FIELDS
        })

        return filters


class SearchInvestmentProjectAPIView(SearchInvestmentProjectParams, SearchAPIView):
    """Filtered investment project search view."""


class SearchInvestmentProjectExportAPIView(SearchInvestmentProjectParams, SearchExportAPIView):
    """Filtered investment project search export view."""
