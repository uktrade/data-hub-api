from django.contrib.postgres.aggregates import ArrayAgg

from datahub.core.query_utils import (
    get_aggregate_subquery,
    get_array_agg_subquery,
)
from datahub.dataset.core.views import BaseFilterDatasetView
from datahub.dbmaintenance.utils import parse_date
from datahub.event.models import Event
from datahub.metadata.query_utils import get_service_name_subquery


class EventsDatasetView(BaseFilterDatasetView):
    """
    An APIView that provides 'get' action to return desired fields for
    Events Dataset to be consumed by Data-flow periodically. Data-flow uses
    response result to insert data into Dataworkspace through its defined API endpoints.
    """

    def get_dataset(self, request):
        """Returns a list of all interaction records"""
        queryset = Event.objects.annotate(
            service_name=get_service_name_subquery('service'),
            team_ids=get_aggregate_subquery(
                Event,
                ArrayAgg('teams__id', ordering=('teams__id',)),
            ),
            related_programme_names=get_array_agg_subquery(
                Event.related_programmes.through,
                'event',
                'programme__name',
                ordering=('programme__name',),
            ),
        ).values(
            'address_1',
            'address_2',
            'address_country__name',
            'address_county',
            'address_postcode',
            'address_town',
            'created_by_id',
            'created_on',
            'disabled_on',
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
            'related_programme_names',
        )
        updated_since = request.GET.get('updated_since')
        if updated_since:
            updated_since_date = parse_date(updated_since)
            if updated_since_date:
                queryset = queryset.filter(modified_on__gt=updated_since_date)

        return queryset
