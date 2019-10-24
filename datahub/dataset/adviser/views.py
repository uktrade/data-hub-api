from datahub.company.models.adviser import Advisor as Adviser
from datahub.dataset.adviser.pagination import AdvisersDatasetViewCursorPagination
from datahub.dataset.core.views import BaseDatasetView


class AdvisersDatasetView(BaseDatasetView):
    """
    An APIView that provides 'get' action which queries and returns desired fields for
    Advisers Dataset to be consumed by Data-flow periodically. Data-flow uses response result
    to insert data into Dataworkspace through its defined API endpoints.
    """

    pagination_class = AdvisersDatasetViewCursorPagination

    def get_dataset(self):
        """Returns list of Advisers Dataset records"""
        return Adviser.objects.values(
            'id',
            'date_joined',
            'first_name',
            'last_name',
            'telephone_number',
            'contact_email',
            'dit_team_id',
            'is_active',
        )
