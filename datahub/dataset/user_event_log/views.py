from django.db.models import F

from datahub.dataset.core.views import BaseFilterDatasetView
from datahub.dbmaintenance.utils import parse_date
from datahub.user_event_log.models import UserEvent


class UserEventsView(BaseFilterDatasetView):
    """
    An APIView that provides 'get' action to return desired fields for
    User Events Log Dataset to be consumed by Data-flow periodically. Data-flow uses
    response result to insert data into Dataworkspace through its defined API endpoints.
    """

    def get_dataset(self, request):
        """Returns a list of all interaction records"""
        queryset = UserEvent.objects.values(
            'adviser__id',
            'type',
            'api_url_path',
            created_on=F('timestamp'),
        )
        updated_since = request.GET.get('updated_since')
        if updated_since:
            updated_since_date = parse_date(updated_since)
            if updated_since_date:
                queryset = queryset.filter(modified_on__gt=updated_since_date)

        return queryset
