import datetime

from django.db.models import Case, Max, When
from django.db.models import CharField
from django.db.models.functions import Cast

from opensearch_dsl.query import (
    Bool,
    Exists,
    Range,
    Term,
)

from datahub.company.models import Company as DBCompany
from datahub.core.constants import InvestmentProjectStage
from datahub.core.query_utils import (
    get_aggregate_subquery,
    get_choices_as_case_expression,
    get_front_end_url_expression,
    get_full_name_expression,
    get_string_agg_subquery,
)
from datahub.investment.project.models import InvestmentProject as DBInvestmentProject
from datahub.investment.project.models import InvestmentProjectStageLog
from datahub.investment.project.query_utils import get_project_code_expression
from datahub.metadata.query_utils import get_sector_name_subquery
from datahub.search.investment import InvestmentSearchApp
from datahub.search.investment.serializers import SearchInvestmentProjectQuerySerializer
from datahub.search.views import register_v3_view, SearchAPIView, SearchExportAPIView


class SearchInvestmentProjectAPIViewMixin:
    """Defines common settings."""

    search_app = InvestmentSearchApp
    serializer_class = SearchInvestmentProjectQuerySerializer
    es_sort_by_remappings = {
        'name': 'name.keyword',
    }

    FILTER_FIELDS = (
        'adviser',
        'client_relationship_manager',
        'country_investment_originates_from',
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
        'level_of_involvement_simplified',
        'likelihood_to_land',
        'gross_value_added_start',
        'gross_value_added_end',
    )

    REMAP_FIELDS = {
        'client_relationship_manager': 'client_relationship_manager.id',
        'investment_type': 'investment_type.id',
        'investor_company': 'investor_company.id',
        'sector': 'sector.id',
        'stage': 'stage.id',
        'likelihood_to_land': 'likelihood_to_land.id',
        'uk_region_location': 'uk_region_locations.id',
        'country_investment_originates_from': 'country_investment_originates_from.id',
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
        'investor_company_country': [
            'investor_company_country.id',
            'country_investment_originates_from.id',
        ],
    }

    def get_extra_filters(self, validated_data):
        """Apply financial year filter."""
        # TODO: remove financial year start filter once land date filter has been
        # implemented and tested on frontend
        financial_year_start_filter = Bool(
            should=[
                Bool(
                    should=[
                        # Non-prospects use actual land date, falling back to estimated land date
                        Bool(
                            should=[
                                Bool(
                                    must=Range(
                                        estimated_land_date={
                                            'gte': datetime.date(
                                                year=financial_year_start,
                                                month=4,
                                                day=1,
                                            ),
                                            'lt': datetime.date(
                                                year=financial_year_start + 1,
                                                month=4,
                                                day=1,
                                            ),
                                        },
                                    ),
                                    must_not=Exists(field='actual_land_date'),
                                ),
                                Range(
                                    actual_land_date={
                                        'gte': datetime.date(
                                            year=financial_year_start,
                                            month=4,
                                            day=1,
                                        ),
                                        'lt': datetime.date(
                                            year=financial_year_start + 1,
                                            month=4,
                                            day=1,
                                        ),
                                    },
                                ),
                            ],
                            must_not=Term(
                                **{'stage.id': InvestmentProjectStage.prospect.value.id},
                            ),
                        ),
                        # Prospects appear in all financial years from the created date
                        Bool(
                            must=[
                                Range(
                                    created_on={
                                        'lte': datetime.date(
                                            year=financial_year_start,
                                            month=4,
                                            day=1,
                                        ),
                                    },
                                ),
                                Term(**{'stage.id': InvestmentProjectStage.prospect.value.id}),
                            ],
                        ),
                    ],
                )
                for financial_year_start in validated_data.get('financial_year_start', [])
            ],
        )
        land_date_filter = Bool(
            should=[
                Bool(
                    should=[
                        Bool(
                            must=Range(
                                estimated_land_date={
                                    'gte': datetime.date(
                                        year=financial_year_start,
                                        month=4,
                                        day=1,
                                    ),
                                    'lt': datetime.date(
                                        year=financial_year_start + 1,
                                        month=4,
                                        day=1,
                                    ),
                                },
                            ),
                            must_not=Exists(field='actual_land_date'),
                        ),
                        Range(
                            actual_land_date={
                                'gte': datetime.date(year=financial_year_start, month=4, day=1),
                                'lt': datetime.date(year=financial_year_start + 1, month=4, day=1),
                            },
                        ),
                    ],
                )
                for financial_year_start in validated_data.get(
                    'land_date_financial_year_start',
                    [],
                )
            ],
        )
        return Bool(must=[financial_year_start_filter, land_date_filter])


@register_v3_view()
class SearchInvestmentProjectAPIView(SearchInvestmentProjectAPIViewMixin, SearchAPIView):
    """Filtered investment project search view."""

    def get_base_query(self, request, validated_data):
        """Add aggregations to show the number of projects at each stage."""
        investor_company_ids = validated_data.get('investor_company')

        if investor_company_ids:
            investor_companies = DBCompany.objects.filter(id__in=investor_company_ids)
            if validated_data.get('include_parent_companies'):
                investor_company_ids.extend(self.get_parent_company_ids(investor_companies))

            if validated_data.get('include_subsidiary_companies'):
                investor_company_ids.extend(self.get_sibling_company_ids(investor_companies))

            validated_data['investor_company'] = investor_company_ids
        print('investor_company_ids:', investor_company_ids)
        base_query = super().get_base_query(request, validated_data)
        if validated_data.get('show_summary'):
            base_query.aggs.bucket('stage', 'terms', field='stage.id')
        return base_query

    def get_sibling_company_ids(self, investor_companies):
        """Get a list of all sibling company id's"""

        # get all company id's where the global ultimate duns number is equal to this
        # companies duns number
        sibling_company_ids = []
        duns_ids = investor_companies.exclude(duns_number__isnull=True).values_list(
            'duns_number',
            flat=True,
        )
        global_ultimate_duns_sibling_ids = DBCompany.objects.filter(
            global_ultimate_duns_number__in=duns_ids,
        ).values_list('id', flat=True)
        sibling_company_ids.extend(global_ultimate_duns_sibling_ids)

        #  get all company id's where the global headquarters is equal to this company id
        global_headquarter_sibling_ids = DBCompany.objects.filter(
            global_headquarters__in=investor_companies,
        ).values_list('id', flat=True)
        sibling_company_ids.extend(global_headquarter_sibling_ids)

        return sibling_company_ids

    def get_parent_company_ids(self, investor_companies):
        """Get a list of all parent company id's"""
        parent_company_ids = []
        global_headquarters_ids = []
        global_ultimate_duns_numbers = []

        parent_companies = investor_companies.exclude(
            global_headquarters__isnull=True,
            global_ultimate_duns_number__exact='',
        ).values_list('global_ultimate_duns_number', 'global_headquarters', named=True)

        for parent_company in parent_companies:
            if parent_company.global_headquarters:
                global_headquarters_ids.append(parent_company.global_headquarters)
            if parent_company.global_ultimate_duns_number:
                global_ultimate_duns_numbers.append(
                    parent_company.global_ultimate_duns_number,
                )

        #  if there are any global headquarters ids, append them to the original list
        if global_headquarters_ids:
            parent_company_ids.extend(global_headquarters_ids)

        if global_ultimate_duns_numbers:
            # if there are any global ultimate duns numbers, get their company id's and
            # append them to the original list
            dnb_to_ids = DBCompany.objects.filter(
                duns_number__in=global_ultimate_duns_numbers,
            ).values_list(
                'id',
                flat=True,
            )
            parent_company_ids.extend(dnb_to_ids)
        return parent_company_ids

    def enhance_response(self, results, response, validated_data):
        """Add summary data to the response."""
        if 'stage' not in results.aggs:
            return response

        response['summary'] = {
            InvestmentProjectStage.prospect.name: {
                'label': 'Prospect',
                'id': InvestmentProjectStage.prospect.value.id,
                'value': 0,
            },
            InvestmentProjectStage.assign_pm.name: {
                'label': 'Assign PM',
                'id': InvestmentProjectStage.assign_pm.value.id,
                'value': 0,
            },
            InvestmentProjectStage.active.name: {
                'label': 'Active',
                'id': InvestmentProjectStage.active.value.id,
                'value': 0,
            },
            InvestmentProjectStage.verify_win.name: {
                'label': 'Verify Win',
                'id': InvestmentProjectStage.verify_win.value.id,
                'value': 0,
            },
            InvestmentProjectStage.won.name: {
                'label': 'Won',
                'id': InvestmentProjectStage.won.value.id,
                'value': 0,
                'last_won_project': {
                    'id': None,
                    'last_changed': None,
                    'name': None,
                },
            },
        }
        for stage_summary in results.aggs['stage'].buckets:
            stage = InvestmentProjectStage.get_by_id(stage_summary['key'])
            if stage is not None and stage.name in response['summary']:
                if (
                    stage.value.id == InvestmentProjectStage.won.value.id
                    and 'investor_company' in validated_data
                ):
                    investor_company_id = validated_data['investor_company'][0]

                    project_stage_log = (
                        InvestmentProjectStageLog.objects.filter(
                            stage_id=InvestmentProjectStage.won.value.id,
                        )
                        .filter(
                            investment_project__investor_company_id=investor_company_id,
                        )
                        .select_related('investment_project')
                        .order_by('-created_on')
                        .first()
                    )

                    response['summary'][stage.name]['last_won_project'][
                        'id'
                    ] = project_stage_log.investment_project.id
                    response['summary'][stage.name]['last_won_project'][
                        'name'
                    ] = project_stage_log.investment_project.name
                    response['summary'][stage.name]['last_won_project'][
                        'last_changed'
                    ] = project_stage_log.created_on
                response['summary'][stage.name]['value'] = stage_summary['doc_count']

        return response


@register_v3_view(sub_path='export')
class SearchInvestmentExportAPIView(SearchInvestmentProjectAPIViewMixin, SearchExportAPIView):
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
            ordering=('team_members__adviser__first_name', 'team_members__adviser__last_name'),
        ),
        delivery_partner_names=get_string_agg_subquery(
            DBInvestmentProject,
            Cast('delivery_partners__name', CharField()),
        ),
        uk_region_location_names=get_string_agg_subquery(
            DBInvestmentProject,
            Cast('uk_region_locations__name', CharField()),
        ),
        actual_uk_region_names=get_string_agg_subquery(
            DBInvestmentProject,
            Cast('actual_uk_regions__name', CharField()),
        ),
        investor_company_global_account_manager=Case(
            When(
                investor_company__global_headquarters__isnull=False,
                then=get_full_name_expression(
                    'investor_company__global_headquarters__one_list_account_owner',
                ),
            ),
            default=get_full_name_expression('investor_company__one_list_account_owner'),
        ),
        client_relationship_manager_name=get_full_name_expression('client_relationship_manager'),
        project_manager_name=get_full_name_expression('project_manager'),
        project_assurance_adviser_name=get_full_name_expression('project_assurance_adviser'),
    )

    @property
    def field_titles(self):
        """
        Returns field titles for CSV export

        There is implicit ordering here, guaranteed for python >= 3.7 to be insertion order
        This is a property because we don't want it to evaluate prior to database instantiation
        """
        field_titles = {
            'created_on': 'Date created',
            'computed_project_code': 'Project reference',
            'name': 'Project name',
            'investor_company__name': 'Investor company',
            'investor_company__address_town': 'Investor company town or city',
        }

        field_titles.update(
            {
                'investor_company__address_area__name': 'Investor company area',
                'country_investment_originates_from__name': 'Country of origin',
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
                'likelihood_to_land__name': 'Likelihood to land',
                'fdi_type__name': 'FDI type',
                'foreign_equity_investment': 'Foreign equity investment',
                'gva_multiplier__multiplier': 'GVA multiplier',
                'gross_value_added': 'GVA',
            },
        )
        return field_titles
