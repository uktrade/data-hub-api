from datahub.company.models import Company
from datahub.dataset.company_future_interest_countries.pagination import \
    CompanyFutureInterestCountriesDatasetViewCursorPagination
from datahub.dataset.core.views import BaseDatasetView


class CompanyFutureInterestCountriesDatasetView(BaseDatasetView):
    """
    A GET API view to return the data for all company future countries of interest
    as required for syncing by Data-flow periodically.
    Data-flow uses the resulting response to insert data into Data workspace which can
    then be queried to create custom reports for users.
    """

    pagination_class = CompanyFutureInterestCountriesDatasetViewCursorPagination

    def get_dataset(self):
        """Returns list of Company Future Interest Countries  records"""
        return Company.objects.values(
            'id',
            'future_interest_countries__name',
            'future_interest_countries__iso_alpha2_code',
        )
