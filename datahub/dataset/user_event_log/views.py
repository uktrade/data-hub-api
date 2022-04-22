from django.contrib.postgres.aggregates import ArrayAgg

from datahub.core.query_utils import get_aggregate_subquery
from datahub.dataset.core.views import BaseDatasetView
from datahub.metadata.query_utils import get_service_name_subquery
from datahub.user_event_log.models import UserEvent


class UserEventsView(BaseDatasetView):
    """
    An APIView that provides 'get' action to return desired fields for
    User Events Log Dataset to be consumed by Data-flow periodically. Data-flow uses
    response result to insert data into Dataworkspace through its defined API endpoints.
    """

    def get_dataset(self):
        """Returns a list of all interaction records"""
        return UserEvent.objects.annotate(
            service_name=get_service_name_subquery('service'),
            team_ids=get_aggregate_subquery(
                UserEvent,
                ArrayAgg('teams__id', ordering=('teams__id',)),
            ),
        ).values(
            'timestamp',
            'adviser__id',
            'type',
            'api_url_path',
        )
