from django.db.models import Prefetch


from datahub.investment.models import (
    InvestmentProject as DBInvestmentProject,
    InvestmentProjectTeamMember as DBInvestmentProjectTeamMember
)
from datahub.investment.permissions import InvestmentProjectAssociationChecker, Permissions

from .models import InvestmentProject
from .views import SearchInvestmentProjectAPIView, SearchInvestmentProjectExportAPIView

from ..apps import SearchApp


class InvestmentSearchApp(SearchApp):
    """SearchApp for investment"""

    name = 'investment_project'
    ESModel = InvestmentProject
    view = SearchInvestmentProjectAPIView
    export_view = SearchInvestmentProjectExportAPIView
    permission_required = (
        f'investment.{Permissions.read_all}',
        f'investment.{Permissions.read_associated}'
    )
    queryset = DBInvestmentProject.objects.prefetch_related(
        'archived_by',
        'average_salary',
        'business_activities',
        'client_contacts',
        'client_relationship_manager',
        'competitor_countries',
        'fdi_type',
        'intermediate_company',
        'investment_type',
        'investmentprojectcode',
        'investor_company',
        'investor_type',
        'level_of_involvement',
        'project_assurance_adviser',
        'project_manager',
        'referral_source_activity',
        'referral_source_activity_marketing',
        'referral_source_activity_website',
        'referral_source_adviser',
        'sector',
        'specific_programme',
        'strategic_drivers',
        'stage',
        'uk_company',
        'uk_region_locations',
        Prefetch('team_members',
                 queryset=DBInvestmentProjectTeamMember.objects.prefetch_related('adviser')),
    )

    def get_permission_filters(self, request):
        """
        Gets permission filter arguments.

        If a user only has permission to access projects associated to their team, this returns
        the filters that should be applied to only return those projects.
        """
        checker = InvestmentProjectAssociationChecker()

        if not checker.should_apply_restrictions(request, 'list', DBInvestmentProject):
            return None

        dit_team_id = str(request.user.dit_team_id) if request.user else None
        filters = {
            f'{field}.dit_team.id': dit_team_id
            for field in DBInvestmentProject.ASSOCIATED_ADVISER_TO_ONE_FIELDS
        }

        filters.update({
            f'{field.es_field_name}.dit_team.id': dit_team_id
            for field in DBInvestmentProject.ASSOCIATED_ADVISER_TO_MANY_FIELDS
        })

        return filters
