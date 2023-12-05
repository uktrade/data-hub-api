from datahub.company_referral.models import CompanyReferral
from datahub.dataset.core.views import BaseFilterDatasetView
from datahub.dataset.utils import filter_data_by_date


class CompanyReferralDatasetView(BaseFilterDatasetView):
    """
    A GET API view to return the data for all company referrals for syncing
    by data flow periodically.
    """

    def get_dataset(self, request):
        """Returns list of CompanyReferral records"""
        queryset = CompanyReferral.objects.values(
            'company_id',
            'completed_by_id',
            'completed_on',
            'contact_id',
            'created_on',
            'created_by_id',
            'id',
            'interaction_id',
            'notes',
            'recipient_id',
            'status',
            'subject',
        )
        updated_since = request.GET.get('updated_since')
        filtered_queryset = filter_data_by_date(updated_since, queryset)

        return filtered_queryset
