from django.contrib.postgres.aggregates import ArrayAgg

from datahub.core.query_utils import get_aggregate_subquery
from datahub.dataset.core.views import BaseDatasetView
from datahub.event.models import Event
from datahub.metadata.query_utils import get_service_name_subquery


class EventsDatasetView(BaseDatasetView):
    """
    An APIView that provides 'get' action to return desired fields for
    Events Dataset to be consumed by Data-flow periodically. Data-flow uses
    response result to insert data into Dataworkspace through its defined API endpoints.
    """

    def get_dataset(self):
        """Returns a list of all interaction records"""
        return Event.objects.annotate(
            service_name=get_service_name_subquery('service'),
            team_ids=get_aggregate_subquery(
                Event,
                ArrayAgg('teams__id', ordering=('teams__id',)),
            ),
        ).values(
            'address_1',
            'address_2',
            'address_country__name',
            'address_county',
            'address_postcode',
            'address_town',
            'created_on',
            'end_date',
            'event_type__name',
            'id',
            'lead_team_id',
            'location_type__name',
            'name',
            'notes',
            'organiser_id',
            'service_name',
            'start_date',
            'team_ids',
            'uk_region__name',
        )
