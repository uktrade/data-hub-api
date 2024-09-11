from datahub.company_activity.models import CompanyActivity as DBCompanyActivity
from datahub.search.apps import SearchApp
from datahub.search.company_activity.models import CompanyActivity


class CompanyActivitySearchApp(SearchApp):
    """SearchApp for company activity."""

    name = 'company-activity'
    search_model = CompanyActivity
    view_permissions = ('company_activity.view_companyactivity',)
    queryset = DBCompanyActivity.objects.select_related(
        'interaction',
    )
