from datahub.dataset.core.views import BaseDatasetView
from datahub.dataset.team.pagination import TeamsDatasetViewCursorPagination
from datahub.metadata.models import Team


class TeamsDatasetView(BaseDatasetView):
    """
    An APIView that provides 'get' action which queries and returns desired fields for
    Teams Dataset to be consumed by Data-flow periodically. Data-flow uses response result
    to insert data into Dataworkspace through its defined API endpoints.
    """

    pagination_class = TeamsDatasetViewCursorPagination

    def get_dataset(self):
        """Returns list of Teams Dataset records"""
        return Team.objects.values(
            'id',
            'name',
            'role__name',
            'uk_region__name',
            'country__name',
        )
