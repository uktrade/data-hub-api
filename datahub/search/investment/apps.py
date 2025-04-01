from django.db.models import Prefetch

from datahub.investment.project.models import (
    InvestmentProject as DBInvestmentProject,
)
from datahub.investment.project.models import (
    InvestmentProjectPermission,
    InvestmentProjectTeamMember,
)
from datahub.investment.project.permissions import (
    InvestmentProjectAssociationChecker,
    get_association_filters,
)
from datahub.search.apps import EXCLUDE_ALL, SearchApp
from datahub.search.investment.models import InvestmentProject


class InvestmentSearchApp(SearchApp):
    """SearchApp for investment."""

    name = 'investment_project'
    search_model = InvestmentProject
    # Investment project documents are very large, so the bulk_batch_size is set to a lower value
    # to keep bulk requests below 10 MB.
    # (In some environments, the maximum OpenSearch request size is 10 MB. This is dependent on
    # the AWS EC2 instance type.)
    bulk_batch_size = 1000
    view_permissions = (
        f'investment.{InvestmentProjectPermission.view_all}',
        f'investment.{InvestmentProjectPermission.view_associated}',
    )
    export_permission = f'investment.{InvestmentProjectPermission.export}'
    queryset = DBInvestmentProject.objects.select_related(
        'archived_by',
        'associated_non_fdi_r_and_d_project',
        'average_salary',
        'client_relationship_manager',
        'client_relationship_manager__dit_team',
        'country_investment_originates_from',
        'country_lost_to',
        'created_by',
        'created_by__dit_team',
        'fdi_type',
        'fdi_value',
        'intermediate_company',
        'investment_type',
        'investmentprojectcode',
        'investor_company',
        'investor_company__address_country',
        'investor_type',
        'level_of_involvement',
        'likelihood_to_land',
        'project_assurance_adviser',
        'project_assurance_adviser__dit_team',
        'project_manager',
        'project_manager__dit_team',
        'referral_source_activity',
        'referral_source_activity_marketing',
        'referral_source_activity_website',
        'referral_source_adviser',
        'sector',
        'sector__parent',
        'sector__parent__parent',
        'stage',
        'uk_company',
        'investor_company__one_list_account_owner',
    ).prefetch_related(
        'strategic_drivers',
        'actual_uk_regions',
        'business_activities',
        'client_contacts',
        'delivery_partners',
        'uk_region_locations',
        'interactions',
        'specific_programmes',
        Prefetch(
            'team_members',
            queryset=InvestmentProjectTeamMember.objects.select_related('adviser__dit_team'),
        ),
    )

    @classmethod
    def get_permission_filters(cls, request):
        """Gets permission filter arguments.

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

        return [
            *[(f'{field}.dit_team.id', value) for field, value in to_one_filters],
            *[(f'{field.es_field_name}.dit_team.id', value) for field, value in to_many_filters],
        ]
