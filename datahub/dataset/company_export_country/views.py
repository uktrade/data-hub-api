from datahub.company.models import CompanyExportCountry
from datahub.dataset.company_export_country.pagination import (
    CompanyExportCountryDatasetViewCursorPagination,
)
from datahub.dataset.core.views import BaseDatasetView


class CompanyExportCountryDatasetView(BaseDatasetView):
    """
    A GET API view to return the data for all company export_country
    as required for syncing by Data-flow periodically.
    Data-flow uses the resulting response to insert data into Data workspace which can
    then be queried to create custom reports for users.
    """

    pagination_class = CompanyExportCountryDatasetViewCursorPagination

    def get_dataset(self):
        """Returns list of company_export_country records"""
        return CompanyExportCountry.objects.values(
            'id',
            'company_id',
            'country__name',
            'country__iso_alpha2_code',
            'status',
        )
