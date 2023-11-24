from datahub.company_referral.models import CompanyReferral
from datahub.dataset.core.views import BaseFilterDatasetView
from datahub.dbmaintenance.utils import parse_date


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
        if updated_since:
            updated_since_date = parse_date(updated_since)
            if updated_since_date:
                queryset = queryset.filter(modified_on__gt=updated_since_date)

        return queryset
