from django.db.models import Max

from datahub.core.query_utils import (
    get_aggregate_subquery,
    get_choices_as_case_expression,
    get_front_end_url_expression,
    get_full_name_expression,
    get_string_agg_subquery,
)
from datahub.investment.models import InvestmentProject as DBInvestmentProject
from datahub.investment.query_utils import get_project_code_expression
from datahub.metadata.query_utils import get_sector_name_subquery
from datahub.oauth.scopes import Scope
from datahub.search.investment.models import InvestmentProject
from datahub.search.investment.serializers import SearchInvestmentProjectSerializer
from datahub.search.views import SearchAPIView, SearchExportAPIView


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
            'sector.ancestors.id',
        ],
    }


class SearchInvestmentProjectAPIView(SearchInvestmentProjectParams, SearchAPIView):
    """Filtered investment project search view."""


class SearchInvestmentExportAPIView(SearchInvestmentProjectParams, SearchExportAPIView):
    """Investment project search export view."""

    # Note: Aggregations on related fields are only used via subqueries as they become very
    # expensive in the main query
    queryset = DBInvestmentProject.objects.annotate(
        computed_project_code=get_project_code_expression(),
        status_name=get_choices_as_case_expression(DBInvestmentProject, 'status'),
        link=get_front_end_url_expression('investmentproject', 'pk'),
        date_of_latest_interaction=get_aggregate_subquery(
            DBInvestmentProject,
            Max('interactions__date'),
        ),
        sector_name=get_sector_name_subquery('sector'),
        team_member_names=get_string_agg_subquery(
            DBInvestmentProject,
            get_full_name_expression('team_members__adviser'),
        ),
        delivery_partner_names=get_string_agg_subquery(
            DBInvestmentProject,
            'delivery_partners__name',
        ),
        uk_region_location_names=get_string_agg_subquery(
            DBInvestmentProject,
            'uk_region_locations__name',
        ),
        actual_uk_region_names=get_string_agg_subquery(
            DBInvestmentProject,
            'actual_uk_regions__name',
        ),
        investor_company_global_account_manager=get_full_name_expression(
            'investor_company__one_list_account_owner',
        ),
        client_relationship_manager_name=get_full_name_expression('client_relationship_manager'),
        project_manager_name=get_full_name_expression('project_manager'),
        project_assurance_adviser_name=get_full_name_expression('project_assurance_adviser'),
    )
    field_titles = {
        'created_on': 'Date created',
        'computed_project_code': 'Project reference',
        'name': 'Project name',
        'investor_company__name': 'Investor company',
        'investor_company__registered_address_country__name': 'Country of origin',
        'investment_type__name': 'Investment type',
        'status_name': 'Status',
        'stage__name': 'Stage',
        'link': 'Link',
        'actual_land_date': 'Actual land date',
        'estimated_land_date': 'Estimated land date',
        'fdi_value__name': 'FDI value',
        'sector_name': 'Sector',
        'date_of_latest_interaction': 'Date of latest interaction',
        'project_manager_name': 'Project manager',
        'client_relationship_manager_name': 'Client relationship manager',
        'investor_company_global_account_manager': 'Global account manager',
        'project_assurance_adviser_name': 'Project assurance adviser',
        'team_member_names': 'Other team members',
        'delivery_partner_names': 'Delivery partners',
        'uk_region_location_names': 'Possible UK regions',
        'actual_uk_region_names': 'Actual UK regions',
        'specific_programme__name': 'Specific investment programme',
        'referral_source_activity__name': 'Referral source activity',
        'referral_source_activity_website__name': 'Referral source activity website',
        'total_investment': 'Total investment',
        'number_new_jobs': 'New jobs',
        'average_salary__name': 'Average salary of new jobs',
        'number_safeguarded_jobs': 'Safeguarded jobs',
        'level_of_involvement__name': 'Level of involvement',
        'r_and_d_budget': 'R&D budget',
        'non_fdi_r_and_d_budget': 'Associated non-FDI R&D project',
        'new_tech_to_uk': 'New to world tech',
    }
