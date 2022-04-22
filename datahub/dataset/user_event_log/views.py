from django.db.models import F

from datahub.dataset.core.views import BaseDatasetView
from datahub.user_event_log.models import UserEvent


class UserEventsView(BaseDatasetView):
    """
    An APIView that provides 'get' action to return desired fields for
    User Events Log Dataset to be consumed by Data-flow periodically. Data-flow uses
    response result to insert data into Dataworkspace through its defined API endpoints.
    """

    def get_dataset(self):
        """Returns a list of all interaction records"""
        return UserEvent.objects.values(
            'adviser__id',
            'type',
            'api_url_path',
            created_on=F('timestamp'),
        )
