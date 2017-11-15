from django.db.models import Prefetch


from datahub.investment.models import (
    InvestmentProject as DBInvestmentProject,
    InvestmentProjectTeamMember as DBInvestmentProjectTeamMember
)

from .models import InvestmentProject
from .views import SearchInvestmentProjectAPIView, SearchInvestmentProjectExportAPIView

from ..apps import SearchApp


class InvestmentSearchApp(SearchApp):
    """SearchApp for investment"""

    name = 'investment_project'
    ESModel = InvestmentProject
    view = SearchInvestmentProjectAPIView
    export_view = SearchInvestmentProjectExportAPIView
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
