from django.db.models import Case, NullBooleanField, Value, When
from django.db.models.functions import Concat

from datahub.admin_report.report import QuerySetReport
from datahub.company.models import Advisor


class AllAdvisersReport(QuerySetReport):
    """Admin report for all advisers."""

    id = 'all-advisers'
    name = 'All advisers'
    model = Advisor
    permissions_required = ('company.read_advisor',)
    queryset = Advisor.objects.annotate(
        name=Concat('first_name', Value(' '), 'last_name'),
        is_team_active=Case(
            When(dit_team__disabled_on__isnull=True, dit_team__isnull=False, then=True),
            When(dit_team__disabled_on__isnull=False, then=False),
            default=None,
            output_field=NullBooleanField()
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
