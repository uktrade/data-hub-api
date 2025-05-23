from django.db.models import BooleanField, Case, When

from datahub.admin_report.report import QuerySetReport
from datahub.company.models import Advisor, Company
from datahub.core import constants
from datahub.core.query_utils import get_front_end_url_expression, get_full_name_expression


class AllAdvisersReport(QuerySetReport):
    """Admin report for all advisers."""

    id = 'all-advisers'
    name = 'All advisers'
    model = Advisor
    permissions_required = ('company.view_advisor',)
    queryset = Advisor.objects.annotate(
        name=get_full_name_expression(),
        is_team_active=Case(
            When(dit_team__disabled_on__isnull=True, dit_team__isnull=False, then=True),
            When(dit_team__disabled_on__isnull=False, then=False),
            default=None,
            output_field=BooleanField(null=True),
        ),
    ).order_by(
        'date_joined',
        'pk',
    )
    field_titles = {
        'id': 'Adviser ID',
        'email': 'Username',
        'name': 'Name',
        'contact_email': 'Contact email',
        'is_active': 'Is active',
        'dit_team__name': 'Team',
        'is_team_active': 'Is team active',
        'dit_team__role__name': 'Team role',
    }


class OneListReport(QuerySetReport):
    """Generates the One List."""

    id = 'one-list'
    name = 'One List'
    model = Company
    permissions_required = ('company.view_company',)
    queryset = (
        Company.objects.filter(
            headquarter_type_id=constants.HeadquarterType.ghq.value.id,
            one_list_tier_id__isnull=False,
            one_list_account_owner_id__isnull=False,
        )
        .annotate(
            primary_contact_name=get_full_name_expression('one_list_account_owner'),
            url=get_front_end_url_expression('company', 'pk'),
        )
        .order_by(
            'one_list_tier__order',
            'name',
        )
    )
    field_titles = {
        'name': 'Account Name',
        'one_list_tier__name': 'Tier',
        'sector__segment': 'Sector',
        'primary_contact_name': 'Primary Contact',
        'one_list_account_owner__telephone_number': 'Contact Number',
        'one_list_account_owner__contact_email': 'E-mail',
        'address_country__name': 'Home Market',
        'address_town': 'Town/City',
        'url': 'Data Hub URL',
    }
