from datahub.company.models import CompanyExportCountryHistory
from datahub.dataset.company_export_country_history.pagination import (
    CompanyExportCountryHistoryDatasetViewCursorPagination,
)
from datahub.dataset.core.views import BaseFilterDatasetView
from datahub.dbmaintenance.utils import parse_date


class CompanyExportCountryHistoryDatasetView(BaseFilterDatasetView):
    """
    A GET API view to return the data for all company export_country_history
    as required for syncing by Data-flow periodically.
    Data-flow uses the resulting response to insert data into Data workspace which can
    then be queried to create custom reports for users.
    """

    pagination_class = CompanyExportCountryHistoryDatasetViewCursorPagination

    def get_dataset(self, request):
        """Returns list of company_export_country_history records"""
        queryset = CompanyExportCountryHistory.objects.values(
            'id',
            'company_id',
            'country__name',
            'country__iso_alpha2_code',
            'history_date',
            'history_id',
            'history_type',
            'status',
        )
        updated_since = request.GET.get('updated_since')
        if updated_since:
            updated_since_date = parse_date(updated_since)
            if updated_since_date:
                queryset = queryset.filter(modified_on__gt=updated_since_date)

        return queryset
