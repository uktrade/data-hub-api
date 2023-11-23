from datahub.dataset.core.views import BaseDatasetView
from datahub.dbmaintenance.utils import parse_date
from datahub.interaction.models import InteractionExportCountry


class InteractionsExportCountryDatasetView(BaseDatasetView):
    """
    A GET API view to return all interaction data related to export country
     as required for syncing by Data-flow periodically.
    """

    def get(self, request):
        """Endpoint which serves all records for Interaction export counties Dataset"""
        dataset = self.get_dataset(request)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(dataset, request, view=self)
        self._enrich_data(page)
        return paginator.get_paginated_response(page)

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

        if updated_since:
            updated_since_date = parse_date(updated_since)
            if updated_since_date:
                queryset = queryset.filter(modified_on__gt=updated_since_date)

        return queryset
