from datahub.dataset.core.views import BaseDatasetView
from datahub.interaction.models import InteractionExportCountry


class InteractionsExportCountryDatasetView(BaseDatasetView):
    """
    A GET API view to return all interaction data related to export country
     as required for syncing by Data-flow periodically.
    """

    def get_dataset(self, request):
        """Returns list of company_export_country_history records"""
        updated_since = request.GET.get('updated_since')
        list_of_interaction_export_countries = InteractionExportCountry.objects.values(
            'country__name',
            'country__iso_alpha2_code',
            'created_on',
            'id',
            'interaction__company_id',
            'interaction__id',
            'status',
        )
        if updated_since:
            return list_of_interaction_export_countries.filter('modified_on' > updated_since)
        return list_of_interaction_export_countries
