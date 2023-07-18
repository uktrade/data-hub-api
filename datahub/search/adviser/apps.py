from datahub.company.models import Advisor as DBAdvisor, CompanyPermission
from datahub.search.adviser.models import Adviser
from datahub.search.apps import SearchApp


class AdviserSearchApp(SearchApp):
    """SearchApp for adviser."""

    name = 'adviser'
    search_model = Adviser
    view_permissions = (f'company.{CompanyPermission.view_company}',)
    queryset = DBAdvisor.objects.select_related(
        'dit_team',
    )
