from datahub.company.models import CompanyExportCountry
from datahub.dataset.core.views import BaseDatasetView


class CompanyExportToCountriesDatasetView(BaseDatasetView):
    """
    A GET API view to return the data for all company export_to_countries
    as required for syncing by Data-flow periodically.
    Data-flow uses the resulting response to insert data into Data workspace which can
    then be queried to create custom reports for users.
    """

    def get_dataset(self):
        """Returns list of company_export_to_countries records"""
        return CompanyExportCountry.objects.filter(
            status=CompanyExportCountry.Status.CURRENTLY_EXPORTING,
        ).values(
            'id',
            'company_id',
            'country__name',
            'country__iso_alpha2_code',
            'created_on',
        )
