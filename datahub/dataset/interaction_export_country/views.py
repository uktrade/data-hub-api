from datahub.dataset.core.views import BaseDatasetView
from datahub.interaction.models import InteractionExportCountry


class InteractionsExportCountryDatasetView(BaseDatasetView):
    """
    A GET API view to return all interaction data related to export country
     as required for syncing by Data-flow periodically.
    """

    def get_dataset(self):
        """Returns list of company_export_country_history records"""
        return InteractionExportCountry.objects.values(
            'country__name',
            'country__iso_alpha2_code',
            'created_on',
            'id',
            'interaction__company_id',
            'interaction__id',
            'status',
        )
