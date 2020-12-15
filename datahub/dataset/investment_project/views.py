from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import OuterRef, Subquery

from datahub.core.constants import InvestmentProjectStage as Stage
from datahub.core.query_utils import (
    get_aggregate_subquery,
    get_empty_string_if_null_expression,
)
from datahub.core.query_utils import (
    get_array_agg_subquery,
)
from datahub.dataset.core.views import BaseDatasetView
from datahub.dataset.investment_project.pagination import (
    InvestmentProjectActivityDatasetViewCursorPagination,
)
from datahub.investment.project.models import (
    InvestmentProject,
    InvestmentProjectStageLog,
)
from datahub.investment.project.query_utils import get_project_code_expression
from datahub.investment.project.report.spi import get_spi_report_queryset
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
            actual_uk_region_names=get_array_agg_subquery(
                InvestmentProject.actual_uk_regions.through,
                'investmentproject',
                'ukregion__name',
                ordering=('ukregion__name',),
            ),
            business_activity_names=get_array_agg_subquery(
                InvestmentProject.business_activities.through,
                'investmentproject',
                'investmentbusinessactivity__name',
                ordering=('investmentbusinessactivity__name',),
            ),
            competing_countries=get_aggregate_subquery(
                InvestmentProject,
                ArrayAgg('competitor_countries__name', ordering=('competitor_countries__name',)),
            ),
            delivery_partner_names=get_array_agg_subquery(
                InvestmentProject.delivery_partners.through,
                'investmentproject',
                'investmentdeliverypartner__name',
                ordering=('investmentdeliverypartner__name',),
            ),
            investor_company_sector=get_sector_name_subquery('investor_company__sector'),
            level_of_involvement_name=get_empty_string_if_null_expression(
                'level_of_involvement__name',
            ),
            project_first_moved_to_won=Subquery(
                InvestmentProjectStageLog.objects.filter(
                    investment_project_id=OuterRef('pk'),
                    stage_id=Stage.won.value.id).order_by('created_on').values('created_on')[:1],
            ),
            project_reference=get_project_code_expression(),
            strategic_driver_names=get_array_agg_subquery(
                InvestmentProject.strategic_drivers.through,
                'investmentproject',
                'investmentstrategicdriver__name',
                ordering=('investmentstrategicdriver__name',),
            ),
            sector_name=get_sector_name_subquery('sector'),
            team_member_ids=get_aggregate_subquery(
                InvestmentProject,
                ArrayAgg('team_members__adviser_id', ordering=('team_members__id',)),
            ),
            uk_company_sector=get_sector_name_subquery('uk_company__sector'),
            uk_region_location_names=get_array_agg_subquery(
                InvestmentProject.uk_region_locations.through,
                'investmentproject',
                'ukregion__name',
                ordering=('ukregion__name',),
            ),
        ).values(
            'actual_land_date',
            'actual_uk_region_names',
            'address_1',
            'address_2',
            'address_town',
            'address_postcode',
            'anonymous_description',
            'associated_non_fdi_r_and_d_project_id',
            'average_salary__name',
            'business_activity_names',
            'client_relationship_manager_id',
            'client_requirements',
            'competing_countries',
            'country_investment_originates_from_id',
            'country_investment_originates_from__name',
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
            'project_first_moved_to_won',
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
            'uk_region_location_names',
        )


class InvestmentProjectsActivityDatasetView(BaseDatasetView):
    """
    An APIView that provides 'get' action which queries and returns desired fields
    for Investment Projects Activity Dataset to be consumed by Data-flow periodically.

    Activity contains SPI report records and it is linked to Investment Project by Data Hub ID.
    Because of the way the report is generated, the relevant SPI report fields are attached to
    Investment Project record in the 'InvestmentProjectActivityDatasetViewCursorPagination'
    pagination class and at the same time all other fields are being left out.
    """

    pagination_class = InvestmentProjectActivityDatasetViewCursorPagination

    def get_dataset(self):
        """Get dataset."""
        return get_spi_report_queryset()
