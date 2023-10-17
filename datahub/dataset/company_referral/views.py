from datahub.company_referral.models import CompanyReferral
from datahub.dataset.core.views import BaseDatasetView


class CompanyReferralDatasetView(BaseDatasetView):
    """
    A GET API view to return the data for all company referrals for syncing
    by data flow periodically.
    """

    def get_dataset(self, request):
        """Returns list of CompanyReferral records"""
        updated_since = request.GET.get('updated_since')
        list_of_company_referrals = CompanyReferral.objects.values(
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
        if updated_since:
            return list_of_company_referrals.filter('modified_on' > updated_since)
        return list_of_company_referrals
