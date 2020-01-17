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
    view_permissions = (f'company.{CompanyPermission.view_company}',)
    export_permission = f'company.{CompanyPermission.export_company}'
    queryset = DBCompanyExportCountryHistory.objects.annotate().select_related(
        'history_user',
        'country',
        'company',
    )
