from datahub.company_referral.models import CompanyReferral
from datahub.dataset.core.views import BaseDatasetView


class CompanyReferralDatasetView(BaseDatasetView):
    """
    A GET API view to return the data for all company referrals for syncing
    by data flow periodically.
    """

    def get_dataset(self):
        """Returns list of CompanyReferral records"""
        return CompanyReferral.objects.values(
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
