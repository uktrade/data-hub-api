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

    def get_dataset(self, request):
        """Returns list of Teams Dataset records"""
        updated_since = request.GET.get('updated_since')
        list_of_teams = Team.objects.values(
            'country__name',
            'disabled_on',
            'id',
            'name',
            'role__name',
            'uk_region__name',
        )
        if updated_since:
            return list_of_teams.filter('modified_on' > updated_since)
        return list_of_teams
