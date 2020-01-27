from datahub.company.models import (
    CompanyExportCountryHistory as DBCompanyExportCountryHistory,
    CompanyPermission,
)
from datahub.search.apps import SearchApp
from datahub.search.exportcountryhistory.models import ExportCountryHistory


class ExportCountryHistoryApp(SearchApp):
    """SearchApp for export countries history timeline"""

    name = 'export-country-history'
    es_model = ExportCountryHistory
    exclude_from_global_search = True
    view_permissions = (f'company.{CompanyPermission.view_company}',)
    queryset = DBCompanyExportCountryHistory.objects.select_related(
        'history_user',
        'country',
        'company',
    )
