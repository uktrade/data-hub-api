from datahub.dataset.core.views import BaseDatasetView
from datahub.dataset.team.pagination import TeamsDatasetViewCursorPagination
from datahub.dbmaintenance.utils import parse_date
from datahub.metadata.models import Team


class TeamsDatasetView(BaseDatasetView):
    """
    An APIView that provides 'get' action which queries and returns desired fields for
    Teams Dataset to be consumed by Data-flow periodically. Data-flow uses response result
    to insert data into Dataworkspace through its defined API endpoints.
    """

    pagination_class = TeamsDatasetViewCursorPagination

    def get(self, request):
        """Endpoint which serves all records for Teams Dataset"""
        dataset = self.get_dataset(request)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(dataset, request, view=self)
        self._enrich_data(page)
        return paginator.get_paginated_response(page)

    def get_dataset(self, request):
        """Returns list of Teams Dataset records"""
        queryset = Team.objects.values(
            'country__name',
            'disabled_on',
            'id',
            'name',
            'role__name',
            'uk_region__name',
        )
        updated_since = request.GET.get('updated_since')

        if updated_since:
            updated_since_date = parse_date(updated_since)
            if updated_since_date:
                queryset = queryset.filter(modified_on__gt=updated_since_date)

        return queryset
