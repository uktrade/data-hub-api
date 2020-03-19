from datahub.company.models import CompanyExportCountryHistory
from datahub.dataset.company_export_country_history.pagination import (
    CompanyExportCountryHistoryDatasetViewCursorPagination,
)
from datahub.dataset.core.views import BaseDatasetView


class CompanyExportCountryHistoryDatasetView(BaseDatasetView):
    """
    A GET API view to return the data for all company export_country_history
    as required for syncing by Data-flow periodically.
    Data-flow uses the resulting response to insert data into Data workspace which can
    then be queried to create custom reports for users.
    """

    pagination_class = CompanyExportCountryHistoryDatasetViewCursorPagination

    def get_dataset(self):
        """Returns list of company_export_country_history records"""
        return CompanyExportCountryHistory.objects.values(
            'id',
            'company_id',
            'country__name',
            'country__iso_alpha2_code',
            'history_date',
            'history_id',
            'history_type',
            'status',
        )
