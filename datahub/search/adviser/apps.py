from datahub.company.models import Advisor as DBAdvisor, AdvisorPermission
from datahub.search.adviser.models import Adviser
from datahub.search.apps import SearchApp


class AdviserSearchApp(SearchApp):
    """SearchApp for adviser."""

    name = 'adviser'
    search_model = Adviser
    view_permissions = (f'company.{AdvisorPermission.view_advisor}',)
    queryset = DBAdvisor.objects.select_related(
        'dit_team',
    )
