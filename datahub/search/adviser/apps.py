from django.db.models import Max

from datahub.company.models import Advisor as DBAdvisor, CompanyPermission
from datahub.core.query_utils import get_aggregate_subquery
from datahub.search.apps import SearchApp
from datahub.search.adviser.models import Adviser


class AdviserSearchApp(SearchApp):
    """SearchApp for adviser."""

    name = 'adviser'
    search_model = Adviser
    view_permissions = (f'company.{CompanyPermission.view_company}',)
    queryset = DBAdvisor.objects.select_related(
        'dit_team',
    )
