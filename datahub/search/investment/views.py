from rest_framework.views import APIView

from .models import InvestmentProject
from ..views import SearchWithFiltersAPIMixin


class SearchInvestmentProjectAPIView(SearchWithFiltersAPIMixin, APIView):
    """Filtered investment project search view."""

    entity = InvestmentProject
    with_aggregations = True

    SORT_BY_FIELDS = (
        'actual_land_date',
        'approved_commitment_to_invest',
        'approved_fdi',
        'approved_good_value',
        'approved_high_value',
        'approved_landed',
        'approved_non_fdi',
        'archived',
        'archived_by.name',
        'average_salary.name',
        'business_activities.name',
        'client_cannot_provide_total_investment',
        'client_contacts.name',
        'client_relationship_manager.name',
        'created_on',
        'estimated_land_date',
        'export_revenue',
        'fdi_type.name',
        'foreign_equity_investment',
        'government_assistance',
        'id',
        'intermediate_company.name',
        'investment_type.name',
        'investor_company.name',
        'modified_on',
        'name',
        'nda_signed',
        'new_tech_to_uk',
        'non_fdi_r_and_d_budget',
        'non_fdi_type.name',
        'number_new_jobs',
        'project_assurance_adviser.name',
        'project_code',
        'project_manager.name',
        'project_shareable',
        'r_and_d_budget',
        'referral_source_activity.name',
        'referral_source_activity_event',
        'referral_source_activity_marketing.name',
        'referral_source_activity_website.name',
        'referral_source_advisor.name',
        'sector.name',
        'site_decided',
        'stage.name',
        'team_members.name',
        'total_investment',
        'uk_company.name'
    )

    FILTER_FIELDS = (
        'client_relationship_manager',
        'estimated_land_date_after',
        'estimated_land_date_before',
        'investment_type',
        'investor_company',
        'sector',
        'stage'
    )

    REMAP_FIELDS = {
        'client_relationship_manager': 'client_relationship_manager.id',
        'investment_type': 'investment_type.id',
        'investor_company': 'investor_company.id',
        'sector': 'sector.id',
        'stage': 'stage.id',
    }
