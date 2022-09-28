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
                        'type': [
                            'dit:dataHub:Event',
                        ],
                        'name': event.name,
                        'dit:eventType': {
                            'name': event.event_type.name,
                            'id': event.event_type.id,
                        },
                        'content': event.notes,
                        'startTime': format_date_or_datetime(event.start_date),
                        'endTime': format_date_or_datetime(event.end_date),
                        'url': event.get_absolute_url(),
                        'updated': format_date_or_datetime(event.modified_on),
                        'dit:locationType': {'name': event.location_type.name},
                        'dit:address_1': event.address_1,
                        'dit:address_2': event.address_2,
                        'dit:address_town': event.address_town,
                        'dit:address_county': event.address_county,
                        'dit:address_postcode': event.address_postcode,
                        'dit:address_country': {
                            'name': event.address_country.name,
                            'id': event.address_country.id,
                        },
                        'dit:leadTeam': {'name': event.lead_team.name},
                        'dit:organiser': {
                            'name': event.organiser.name,
                            'id': event.organiser.id,
                        },
                        'dit:disabledOn': event.disabled_on,
                        'dit:service': {'name': event.service.name},
                        'dit:archivedDocumentsUrlPath': event.archived_documents_url_path,
                        'dit:ukRegion': {
                            'name': event.uk_region.name,
                            'id': event.uk_region.id,
                        },
                        'dit:teams': [
                            *[
                                {
                                    'id': f'dit:DataHubTeam:{team.pk}',
                                    'type': ['Group', 'dit:Team'],
                                    'name': team.name,
                                }
                                for team in event.teams.order_by('pk')
                            ],
                        ],
                        'dit:relatedProgrammes': [
                            *[
                                {
                                    'id': f'dit:DataHubEventProgramme:{programme.pk}',
                                    'name': programme.name,
                                }
                                for programme in event.related_programmes.order_by('pk')
                            ],
                        ],
                        'dit:hasRelatedTradeAgreements': event.has_related_trade_agreements,
                        'dit:relatedTradeAgreements':
                        [
                            *[
                                {
                                    'id': f'dit:DataHubTradeAgreement:{trade_agreement.pk}',
                                    'name': trade_agreement.name,
                                }
                                for trade_agreement in
                                event.related_trade_agreements.order_by('pk')
                            ],
                        ],
                    },
                },
            ],
        }


def _get_response(api_client):
    with freeze_time() as frozen_datetime:
        frozen_datetime.tick(datetime.timedelta(seconds=1, microseconds=1))
        response = hawk.get(api_client, get_url('api-v3:activity-stream:events'))
    return response


def run_none_type_tests(api_client):
    response = _get_response(api_client)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_null_event_region(api_client):
    EventFactory(uk_region_id=None)
    run_none_type_tests(api_client)


@pytest.mark.django_db
def test_null_event_organiser(api_client):
    EventFactory(organiser=None)
    run_none_type_tests(api_client)


@pytest.mark.django_db
def test_null_event_lead_team(api_client):
    EventFactory(lead_team_id=None)
    run_none_type_tests(api_client)


@pytest.mark.django_db
def test_null_event_location_type(api_client):
    EventFactory(location_type_id=None)
    run_none_type_tests(api_client)


@pytest.mark.django_db
def test_null_event_service(api_client):
    EventFactory(service_id=None)
    run_none_type_tests(api_client)


@pytest.mark.django_db
def test_trade_agreements_only_shown_if_they_exist(api_client):
    EventFactory(has_related_trade_agreements=True)
    response = _get_response(api_client)

    assert response.status_code == status.HTTP_200_OK
    assert 'dit:relatedTradeAgreements' in response.json()['orderedItems'][0]['object']


@pytest.mark.django_db
def test_trade_agreements_do_not_show_if_they_do_not_exist(api_client):
    EventFactory(has_related_trade_agreements=False)
    response = _get_response(api_client)

    assert response.status_code == status.HTTP_200_OK
    assert 'dit:relatedTradeAgreements' not in response.json()['orderedItems'][0]['object']
