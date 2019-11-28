from django.contrib.postgres.aggregates import ArrayAgg

from datahub.core.query_utils import get_aggregate_subquery, get_empty_string_if_null_expression
from datahub.dataset.core.views import BaseDatasetView
from datahub.dataset.investment_project.query_utils import (
    get_investment_project_to_many_string_agg_subquery,
)
from datahub.investment.project.models import InvestmentProject
from datahub.investment.project.query_utils import get_project_code_expression
from datahub.metadata.query_utils import get_sector_name_subquery


class InvestmentProjectsDatasetView(BaseDatasetView):
    """
    An APIView that provides 'get' action which queries and returns desired fields for
    Investment Projects Dataset to be consumed by Data-flow periodically.
    Data-flow uses response result to insert data into Dataworkspace through its defined
    API endpoints. The goal is presenting various reports to the users out of flattened table
    and let analyst to work on denormalized table to get more meaningful insight.
    """

    def get_dataset(self):
        """Returns list of Investment Projects Dataset records"""
        return InvestmentProject.objects.annotate(
            actual_uk_region_names=get_investment_project_to_many_string_agg_subquery(
                'actual_uk_regions__name',
            ),
            business_activity_names=get_investment_project_to_many_string_agg_subquery(
                'business_activities__name',
            ),
            competing_countries=get_aggregate_subquery(
                InvestmentProject,
                ArrayAgg('competitor_countries__name', ordering=('competitor_countries__name',)),
            ),
            delivery_partner_names=get_investment_project_to_many_string_agg_subquery(
                'delivery_partners__name',
            ),
            investor_company_sector=get_sector_name_subquery('investor_company__sector'),
            level_of_involvement_name=get_empty_string_if_null_expression(
                'level_of_involvement__name',
            ),
            project_reference=get_project_code_expression(),
            strategic_driver_names=get_investment_project_to_many_string_agg_subquery(
                'strategic_drivers__name',
            ),
            sector_name=get_sector_name_subquery('sector'),
            team_member_ids=get_aggregate_subquery(
                InvestmentProject,
                ArrayAgg('team_members__adviser_id', ordering=('team_members__id',)),
            ),
            uk_company_sector=get_sector_name_subquery('uk_company__sector'),
        ).values(
            'actual_land_date',
            'actual_uk_region_names',
            'address_1',
            'address_2',
            'address_town',
            'address_postcode',
            'allow_blank_possible_uk_regions',
            'anonymous_description',
            'associated_non_fdi_r_and_d_project_id',
            'average_salary__name',
            'business_activity_names',
            'client_relationship_manager_id',
            'client_requirements',
            'competing_countries',
            'created_by_id',
            'created_on',
            'delivery_partner_names',
            'description',
            'estimated_land_date',
            'export_revenue',
            'fdi_type__name',
            'fdi_value__name',
            'foreign_equity_investment',
            'government_assistance',
            'gross_value_added',
            'gva_multiplier__multiplier',
            'id',
            'investment_type__name',
            'investor_company_id',
            'investor_company_sector',
            'investor_type__name',
            'level_of_involvement_name',
            'likelihood_to_land__name',
            'modified_by_id',
            'modified_on',
            'name',
            'new_tech_to_uk',
            'non_fdi_r_and_d_budget',
            'number_new_jobs',
            'number_safeguarded_jobs',
            'other_business_activity',
            'project_arrived_in_triage_on',
            'project_assurance_adviser_id',
            'project_manager_id',
            'project_reference',
            'proposal_deadline',
            'r_and_d_budget',
            'referral_source_activity__name',
            'referral_source_activity_marketing__name',
            'referral_source_activity_website__name',
            'sector_name',
            'specific_programme__name',
            'stage__name',
            'status',
            'strategic_driver_names',
            'team_member_ids',
            'total_investment',
            'uk_company_id',
            'uk_company_sector',
        )
