from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import CharField, OuterRef, Subquery, Value
from django.db.models.functions import Cast, Concat

from datahub.core.constants import InvestmentProjectStage as Stage
from datahub.core.query_utils import (
    get_aggregate_subquery,
    get_array_agg_subquery,
    get_empty_string_if_null_expression,
)
from datahub.dataset.core.views import BaseDatasetView, BaseFilterDatasetView
from datahub.dataset.investment_project.pagination import (
    InvestmentProjectActivityDatasetViewCursorPagination,
)
from datahub.dbmaintenance.utils import parse_date
from datahub.investment.project.models import (
    InvestmentProject,
    InvestmentProjectStageLog,
)
from datahub.investment.project.query_utils import get_project_code_expression
from datahub.investment.project.report.spi import get_spi_report_queryset
from datahub.investment_lead.models import EYBLead
from datahub.metadata.query_utils import get_sector_name_subquery


class InvestmentProjectsDatasetView(BaseFilterDatasetView):
    """An APIView that provides 'get' action which queries and returns desired fields for
    Investment Projects Dataset to be consumed by Data-flow periodically.
    Data-flow uses response result to insert data into Dataworkspace through its defined
    API endpoints. The goal is presenting various reports to the users out of flattened table
    and let analyst to work on denormalized table to get more meaningful insight.
    """

    def get_dataset(self, request):
        """Returns list of Investment Projects Dataset records."""
        queryset = InvestmentProject.objects.annotate(
            actual_uk_region_names=get_array_agg_subquery(
                InvestmentProject.actual_uk_regions.through,
                'investmentproject',
                'ukregion__name',
                order_by=('ukregion__name',),
            ),
            business_activity_names=get_array_agg_subquery(
                InvestmentProject.business_activities.through,
                'investmentproject',
                'investmentbusinessactivity__name',
                order_by=('investmentbusinessactivity__name',),
            ),
            competing_countries=get_aggregate_subquery(
                InvestmentProject,
                ArrayAgg('competitor_countries__name', order_by=('competitor_countries__name',)),
            ),
            delivery_partner_names=get_array_agg_subquery(
                InvestmentProject.delivery_partners.through,
                'investmentproject',
                'investmentdeliverypartner__name',
                order_by=('investmentdeliverypartner__name',),
            ),
            investor_company_sector=get_sector_name_subquery('investor_company__sector'),
            level_of_involvement_name=get_empty_string_if_null_expression(
                Cast('level_of_involvement__name', CharField()),
            ),
            project_first_moved_to_won=Subquery(
                InvestmentProjectStageLog.objects.filter(
                    investment_project_id=OuterRef('pk'),
                    stage_id=Stage.won.value.id,
                )
                .order_by('created_on')
                .values('created_on')[:1],
            ),
            project_reference=get_project_code_expression(),
            strategic_driver_names=get_array_agg_subquery(
                InvestmentProject.strategic_drivers.through,
                'investmentproject',
                'investmentstrategicdriver__name',
                order_by=('investmentstrategicdriver__name',),
            ),
            sector_name=get_sector_name_subquery('sector'),
            team_member_ids=get_aggregate_subquery(
                InvestmentProject,
                ArrayAgg('team_members__adviser_id', order_by=('team_members__id',)),
            ),
            uk_company_sector=get_sector_name_subquery('uk_company__sector'),
            uk_region_location_names=get_array_agg_subquery(
                InvestmentProject.uk_region_locations.through,
                'investmentproject',
                'ukregion__name',
                order_by=('ukregion__name',),
            ),
            client_contact_ids=ArrayAgg(
                'client_contacts__id',
                order_by=('client_contacts__id',),
            ),
            client_contact_names=ArrayAgg(
                Concat(
                    'client_contacts__first_name',
                    Value(' '),
                    'client_contacts__last_name',
                ),
                order_by=('client_contacts__first_name', 'client_contacts__last_name'),
            ),
            client_contact_emails=ArrayAgg(
                'client_contacts__email',
                order_by=('client_contacts__email',),
            ),
            specific_programme_names=get_array_agg_subquery(
                InvestmentProject.specific_programmes.through,
                'investmentproject',
                'specificprogramme__name',
                order_by=('specificprogramme__name',),
            ),
            eyb_lead_ids=get_array_agg_subquery(
                model=EYBLead.investment_projects.through,
                join_field_name='investmentproject',
                expression_to_aggregate='eyblead__id',
                order_by=('eyblead__id'),
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
            'client_contact_ids',
            'client_contact_names',
            'client_contact_emails',
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
            'specific_programme_names',
            'stage__name',
            'status',
            'strategic_driver_names',
            'team_member_ids',
            'total_investment',
            'uk_company_id',
            'uk_company_sector',
            'uk_region_location_names',
            'eyb_lead_ids',
        )
        updated_since = request.GET.get('updated_since')

        if updated_since:
            updated_since_date = parse_date(updated_since)
            if updated_since_date:
                queryset = queryset.filter(modified_on__gt=updated_since_date)

        return queryset


class InvestmentProjectsActivityDatasetView(BaseDatasetView):
    """An APIView that provides 'get' action which queries and returns desired fields
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
