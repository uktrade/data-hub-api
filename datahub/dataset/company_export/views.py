from datahub.company.models import CompanyExport
from datahub.core.query_utils import get_array_agg_subquery
from datahub.dataset.core.views import BaseFilterDatasetView
from datahub.dataset.utils import filter_data_by_date
from datahub.metadata.query_utils import get_sector_name_subquery


class CompanyExportDatasetView(BaseFilterDatasetView):
    """
    A GET API view to return pipeline item data for syncing by data-flow periodically.
    """

    def get_dataset(self, request):
        """Returns list of CompanyExport records"""
        queryset = CompanyExport.objects.annotate(
            sector_name=get_sector_name_subquery('sector'),
            contact_ids=get_array_agg_subquery(
                CompanyExport.contacts.through,
                'companyexport',
                'contact_id',
                ordering=('contact__created_on',),
            ),
            team_member_ids=get_array_agg_subquery(
                CompanyExport.team_members.through,
                'companyexport',
                'advisor_id',
                ordering=('advisor__date_joined',),
            ),
        ).values(
            'created_on',
            'modified_on',
            'created_by_id',
            'modified_by_id',
            'archived',
            'archived_on',
            'archived_reason',
            'archived_by_id',
            'id',
            'company_id',
            'title',
            'owner_id',
            'estimated_export_value_years__name',
            'estimated_export_value_amount',
            'estimated_win_date',
            'destination_country__name',
            'destination_country__iso_alpha2_code',
            'export_potential',
            'status',
            'exporter_experience__name',
            'notes',
            'sector_name',
            'contact_ids',
            'team_member_ids',
        )

        updated_since = request.GET.get('updated_since')
        filtered_queryset = filter_data_by_date(updated_since, queryset)

        return filtered_queryset
