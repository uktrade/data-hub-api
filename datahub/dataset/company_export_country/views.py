from datahub.company.models import CompanyExportCountry
from datahub.dataset.core.views import BaseDatasetView


class CompanyExportCountryDatasetView(BaseDatasetView):
    """
    A GET API view to return the data for all company export_country
    as required for syncing by Data-flow periodically.
    Data-flow uses the resulting response to insert data into Data workspace which can
    then be queried to create custom reports for users.
    """

    def get_dataset(self, request):
        """Returns list of company_export_country records"""
        updated_since = request.GET.get('updated_since')
        list_company_export_countries = CompanyExportCountry.objects.values(
            'id',
            'company_id',
            'country__name',
            'country__iso_alpha2_code',
            'created_on',
            'modified_on',
            'status',
        )
        if updated_since:
            return list_company_export_countries.filter('modified_on' > updated_since)
        return list_company_export_countries
