from datahub.dataset.core.views import BaseFilterDatasetView
from datahub.dataset.utils import filter_data_by_date
from datahub.interaction.models import InteractionExportCountry


class InteractionsExportCountryDatasetView(BaseFilterDatasetView):
    """
    A GET API view to return all interaction data related to export country
     as required for syncing by Data-flow periodically.
    """

    def get_dataset(self, request):
        """Returns list of company_export_country_history records"""
        queryset = InteractionExportCountry.objects.values(
            'country__name',
            'country__iso_alpha2_code',
            'created_on',
            'id',
            'interaction__company_id',
            'interaction__id',
            'status',
        )
        updated_since = request.GET.get('updated_since')

        filtered_queryset = filter_data_by_date(updated_since, queryset)

        return filtered_queryset
