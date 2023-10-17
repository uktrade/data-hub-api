from django.db.models import F

from datahub.dataset.core.views import BaseDatasetView
from datahub.user_event_log.models import UserEvent


class UserEventsView(BaseDatasetView):
    """
    An APIView that provides 'get' action to return desired fields for
    User Events Log Dataset to be consumed by Data-flow periodically. Data-flow uses
    response result to insert data into Dataworkspace through its defined API endpoints.
    """

    def get_dataset(self, request):
        """Returns a list of all interaction records"""
        updated_since = request.GET.get('updated_since')
        list_of_user_events = UserEvent.objects.values(
            'adviser__id',
            'type',
            'api_url_path',
            created_on=F('timestamp'),
        )
        if updated_since:
            return list_of_user_events.filter('modified_on' > updated_since)
        return list_of_user_events
