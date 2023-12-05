from datahub.company.models import CompanyExportCountry
from datahub.dataset.core.views import BaseFilterDatasetView
from datahub.dataset.utils import filter_data_by_date


class CompanyExportCountryDatasetView(BaseFilterDatasetView):
    """
    A GET API view to return the data for all company export_country
    as required for syncing by Data-flow periodically.
    Data-flow uses the resulting response to insert data into Data workspace which can
    then be queried to create custom reports for users.
    """

    def get_dataset(self, request):
        """Returns list of company_export_country records"""
        queryset = CompanyExportCountry.objects.values(
            'id',
            'company_id',
            'country__name',
            'country__iso_alpha2_code',
            'created_on',
            'modified_on',
            'status',
        )
        updated_since = request.GET.get('updated_since')
        filtered_queryset = filter_data_by_date(updated_since, queryset)

        return filtered_queryset
