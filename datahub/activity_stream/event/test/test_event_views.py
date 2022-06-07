import datetime

import pytest
from freezegun import freeze_time
from rest_framework import status

from datahub.activity_stream.test import hawk
from datahub.activity_stream.test.utils import get_url
from datahub.core.test_utils import format_date_or_datetime
from datahub.event.test.factories import EventFactory


@pytest.mark.django_db
def test_event_activity(api_client):
    """
    Get a list of Events and test the returned JSON is valid
    """
    start = datetime.datetime(year=2012, month=7, day=12, hour=15, minute=6, second=3)
    with freeze_time(start) as frozen_datetime:
        event = EventFactory()
        frozen_datetime.tick(datetime.timedelta(seconds=1, microseconds=1))
        response = hawk.get(api_client, get_url('api-v3:activity-stream:events'))

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            '@context': 'https://www.w3.org/ns/activitystreams',
            'summary': 'Event',
            'type': 'OrderedCollectionPage',
            'next': 'http://testserver/v3/activity-stream/event'
            + '?cursor=2012-07-12T15%3A06%3A03.000000%2B00%3A00'
            + f'&cursor={str(event.id)}',
            'orderedItems': [
                {
                    'id': f'dit:DataHubEvent:{event.id}:Announce',
                    'type': 'Announce',
                    'published': format_date_or_datetime(event.created_on),
                    'generator': {'name': 'dit:dataHub', 'type': 'Application'},
                    'object': {
                        'id': f'dit:DataHubEvent:{event.id}',
                        'type': ['dit:Event',
                                 ],
                        'name': event.name,
                        'dit:eventType': {'name': event.event_type.name},
                        'content': event.notes,
                        'startTime': format_date_or_datetime(event.start_date),
                        'endTime': format_date_or_datetime(event.end_date),
                        'url': event.get_absolute_url(),
                        'dit:locationType': {'name': event.location_type.name},
                        'dit:address_1': event.address_1,
                        'dit:address_2': event.address_2,
                        'dit:address_town': event.address_town,
                        'dit:address_county': event.address_county,
                        'dit:address_postcode': event.address_postcode,
                        'dit:address_country': {'name': event.address_country.name},
                        'dit:leadTeam': {'name': event.lead_team.name},
                        'dit:organiser': {'name': event.organiser.name},
                        'dit:disabledOn': event.disabled_on,
                        'dit:service': {'name': event.service.name},
                        'dit:archivedDocumentsUrlPath': event.archived_documents_url_path,
                        'dit:ukRegion': {'name': event.uk_region.name},
                    },
                },
            ],
        }
