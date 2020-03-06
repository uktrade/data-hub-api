from datahub.company.models import (
    CompanyExportCountryHistory as DBCompanyExportCountryHistory,
)
from datahub.search.apps import SearchApp
from datahub.search.export_country_history.models import ExportCountryHistory


class ExportCountryHistoryApp(SearchApp):
    """SearchApp for export countries history timeline"""

    name = 'export-country-history'
    es_model = ExportCountryHistory
    exclude_from_global_search = True
    queryset = DBCompanyExportCountryHistory.objects.select_related(
        'history_user',
        'country',
        'company',
    )
