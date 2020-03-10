from datahub.company.models import CompanyExportCountry
from datahub.dataset.core.views import BaseDatasetView


class CompanyFutureInterestCountriesDatasetView(BaseDatasetView):
    """
    A GET API view to return the data for all company future countries of interest
    as required for syncing by Data-flow periodically.
    Data-flow uses the resulting response to insert data into Data workspace which can
    then be queried to create custom reports for users.
    """

    def get_dataset(self):
        """Returns list of Company Future Interest Countries  records"""
        return CompanyExportCountry.objects.filter(
            status=CompanyExportCountry.Status.FUTURE_INTEREST,
        ).values(
            'id',
            'company_id',
            'country__name',
            'country__iso_alpha2_code',
            'created_on',
        )
