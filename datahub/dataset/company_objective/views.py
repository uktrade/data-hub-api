from datahub.company.models import Objective
from datahub.dataset.core.views import BaseDatasetView


class CompanyObjectiveDatasetView(BaseDatasetView):
    """
    A GET API view to return the data for company objectives as required
    for syncing by Data-flow periodically.
    """

    def get_dataset(self):
        """Returns list of CompanyObjective records"""
        return Objective.objects.values(
            'id',
            'company_id',
            'subject',
            'detail',
            'target_date',
            'has_blocker',
            'blocker_description',
            'progress',
            'created_on',
        )
