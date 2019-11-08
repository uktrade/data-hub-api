from datahub.company.models import Company
from datahub.dataset.company_export_to_country.pagination import (
    CompanyExportToCountriesDatasetViewCursorPagination,
)
from datahub.dataset.core.views import BaseDatasetView


class CompanyExportToCountriesDatasetView(BaseDatasetView):
    """
    A GET API view to return the data for all company export_to_countries
    as required for syncing by Data-flow periodically.
    Data-flow uses the resulting response to insert data into Data workspace which can
    then be queried to create custom reports for users.
    """

    pagination_class = CompanyExportToCountriesDatasetViewCursorPagination

    def get_dataset(self):
        """Returns list of company_export_to_countries records"""
        return Company.export_to_countries.through.objects.values(
            'id',
            'company_id',
            'country__name',
            'country__iso_alpha2_code',
        )
