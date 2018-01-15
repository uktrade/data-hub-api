from django.db.models import Prefetch


from datahub.investment.models import (
    InvestmentProject as DBInvestmentProject,
    InvestmentProjectPermission,
    InvestmentProjectTeamMember as DBInvestmentProjectTeamMember,
)
from datahub.investment.permissions import (
    get_association_filters, InvestmentProjectAssociationChecker
)

from .models import InvestmentProject
from .views import SearchInvestmentProjectAPIView, SearchInvestmentProjectExportAPIView

from ..apps import EXCLUDE_ALL, SearchApp


class InvestmentSearchApp(SearchApp):
    """SearchApp for investment"""

    name = 'investment_project'
    ESModel = InvestmentProject
    view = SearchInvestmentProjectAPIView
    export_view = SearchInvestmentProjectExportAPIView
    permission_required = (
        f'investment.{InvestmentProjectPermission.read_all}',
        f'investment.{InvestmentProjectPermission.read_associated}'
    )
    queryset = DBInvestmentProject.objects.prefetch_related(
        'actual_uk_regions',
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

        if not checker.should_apply_restrictions(request, 'list'):
            return None

        if checker.should_exclude_all(request):
            return EXCLUDE_ALL

        dit_team_id = request.user.dit_team_id
        to_one_filters, to_many_filters = get_association_filters(dit_team_id)

        filters = {f'{field}.dit_team.id': value for field, value in to_one_filters}
        filters.update({
            f'{field.es_field_name}.dit_team.id': value for field, value in to_many_filters
        })

        return filters
