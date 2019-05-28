import mohawk
import pytest
from django.conf import settings
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.activity_stream.interaction.serializers import InteractionActivitySerializer
from datahub.core.test_utils import format_date_or_datetime
from datahub.interaction.models import Interaction
from datahub.interaction.test.factories import (
    CompanyInteractionFactory,
    ContactFactory,
    EventServiceDeliveryFactory,
    InteractionDITParticipantFactory,
    InvestmentProjectInteractionFactory,
    ServiceDeliveryFactory,
)


def _url(name):
    return 'http://testserver' + reverse(name)


def _auth_sender(
    url,
    key_id='some-id',
    secret_key='some-secret',
    method='GET',
    content='',
    content_type='',
):
    credentials = {
        'id': key_id,
        'key': secret_key,
        'algorithm': 'sha256',
    }
    return mohawk.Sender(
        credentials,
        url,
        method,
        content=content,
        content_type=content_type,
    )


def _hawk_get(client, url):
    return client.get(
        url,
        content_type='',
        HTTP_AUTHORIZATION=_auth_sender(url).request_header,
        HTTP_X_FORWARDED_FOR='3.3.3.3, 1.2.3.4, 123.123.123.123',
    )


@pytest.mark.parametrize(
    'get_kwargs,expected_json',
    (
        (
            # If the Authorization header isn't passed
            {
                'content_type': '',
                'HTTP_X_FORWARDED_FOR': '1.2.3.4, 123.123.123.123',
            },
            {'detail': 'Authentication credentials were not provided.'},
        ),
        (
            # If the wrong credentials are used
            {
                'content_type': '',
                'HTTP_AUTHORIZATION': _auth_sender(
                    _url('api-v3:activity-stream:interactions'),
                    key_id='incorrect',
                    secret_key='incorrect',
                ).request_header,
                'HTTP_X_FORWARDED_FOR': '1.2.3.4, 123.123.123.123',
            },
            {'detail': 'Incorrect authentication credentials.'},
        ),
    ),
)
@pytest.mark.django_db
def test_401_returned(api_client, get_kwargs, expected_json):
    """If the request isn't Hawk-authenticated, then a 401 is returned."""
    response = api_client.get(
        _url('api-v3:activity-stream:interactions'),
        **get_kwargs,
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == expected_json


@pytest.mark.django_db
def test_403_returned(api_client):
    """
    Test that a 403 is returned if the request is Hawk authenticated but the client doesn't have
    the required scope.
    """
    sender = _auth_sender(
        _url('api-v3:activity-stream:interactions'),
        key_id='test-id-without-scope',
        secret_key='test-key-without-scope',
    )
    response = api_client.get(
        _url('api-v3:activity-stream:interactions'),
        content_type='',
        HTTP_AUTHORIZATION=sender.request_header,
        HTTP_X_FORWARDED_FOR='3.3.3.3, 1.2.3.4, 123.123.123.123',
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {
        'detail': 'You do not have permission to perform this action.',
    }


@pytest.mark.django_db
def test_succeeds_with_valid_credentials(api_client):
    """If the Authorization and X-Forwarded-For headers are correct, then
    the correct, and authentic, data is returned
    """
    sender = _auth_sender(_url('api-v3:activity-stream:interactions'))
    response = api_client.get(
        _url('api-v3:activity-stream:interactions'),
        content_type='',
        HTTP_AUTHORIZATION=sender.request_header,
        HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',
    )
    assert response.status_code == status.HTTP_200_OK

    # Just asserting that accept_response doesn't raise is a bit weak,
    # so we also assert that it raises if the header, content, or
    # content_type are incorrect
    sender.accept_response(
        response_header=response['Server-Authorization'],
        content=response.content,
        content_type=response['Content-Type'],
    )
    with pytest.raises(mohawk.exc.MacMismatch):
        sender.accept_response(
            response_header='Hawk mac="incorrect", hash="incorrect"',
            content=response.content,
            content_type=response['Content-Type'],
        )
    with pytest.raises(mohawk.exc.MisComputedContentHash):
        sender.accept_response(
            response_header=response['Server-Authorization'],
            content='incorrect',
            content_type=response['Content-Type'],
        )
    with pytest.raises(mohawk.exc.MisComputedContentHash):
        sender.accept_response(
            response_header=response['Server-Authorization'],
            content=response.content,
            content_type='incorrect',
        )


@pytest.mark.django_db
def test_interaction_activity(api_client):
    """
    Get a list of interactions and test the returned JSON is valid as per:
    https://www.w3.org/TR/activitystreams-core/
    """
    interaction = CompanyInteractionFactory()
    response = _hawk_get(api_client, _url('api-v3:activity-stream:interactions'))
    assert response.status_code == status.HTTP_200_OK

    assert response.json() == {
        '@context': 'https://www.w3.org/ns/activitystreams',
        'summary': 'Interaction Activities',
        'type': 'OrderedCollectionPage',
        'id': 'http://testserver/v3/activity-stream/interactions',
        'partOf': 'http://testserver/v3/activity-stream/interactions',
        'previous': None,
        'next': None,
        'orderedItems': [
            {
                'id': f'dit:DataHubInteraction:{interaction.id}:Announce',
                'type': 'Announce',
                'published': format_date_or_datetime(interaction.created_on),
                'generator': {'name': 'dit:dataHub', 'type': 'Application'},
                'object': {
                    'id': f'dit:DataHubInteraction:{interaction.id}',
                    'type': ['dit:Event', 'dit:Interaction'],
                    'startTime': format_date_or_datetime(interaction.date),
                    'dit:status': interaction.status,
                    'dit:archived': interaction.archived,
                    'dit:communicationChannel': {'name': interaction.communication_channel.name},
                    'dit:subject': interaction.subject,
                    'dit:service': {'name': interaction.service.name},
                    'attributedTo': [
                        {
                            'id': f'dit:DataHubCompany:{interaction.company.pk}',
                            'dit:dunsNumber': interaction.company.duns_number,
                            'dit:companiesHouseNumber': interaction.company.company_number,
                            'type': ['Organization', 'dit:Company'],
                            'name': interaction.company.name,
                        },
                        *[
                            {
                                'id': f'dit:DataHubAdviser:{participant.adviser.pk}',
                                'type': ['Person', 'dit:Adviser'],
                                'dit:emailAddress':
                                    participant.adviser.contact_email or participant.adviser.email,
                                'name': participant.adviser.name,
                            }
                            for participant in interaction.dit_participants.order_by('pk')
                        ],
                        *[
                            {
                                'id': f'dit:DataHubContact:{contact.pk}',
                                'type': ['Person', 'dit:Contact'],
                                'dit:emailAddress': contact.email,
                                'name': contact.name,
                            }
                            for contact in interaction.contacts.order_by('pk')
                        ],
                    ],
                    'url': interaction.get_absolute_url(),
                },
            },
        ],
    }


@pytest.mark.django_db
def test_interaction_investment_project_activity(api_client):
    """
    Get a list of interactions and test the returned JSON is valid as per:
    https://www.w3.org/TR/activitystreams-core/
    """
    interaction = InvestmentProjectInteractionFactory()
    project = interaction.investment_project
    response = _hawk_get(api_client, _url('api-v3:activity-stream:interactions'))
    assert response.status_code == status.HTTP_200_OK

    assert response.json() == {
        '@context': 'https://www.w3.org/ns/activitystreams',
        'summary': 'Interaction Activities',
        'type': 'OrderedCollectionPage',
        'id': 'http://testserver/v3/activity-stream/interactions',
        'partOf': 'http://testserver/v3/activity-stream/interactions',
        'previous': None,
        'next': None,
        'orderedItems': [
            {
                'id': f'dit:DataHubInteraction:{interaction.id}:Announce',
                'type': 'Announce',
                'published': format_date_or_datetime(interaction.created_on),
                'generator': {'name': 'dit:dataHub', 'type': 'Application'},
                'object': {
                    'id': f'dit:DataHubInteraction:{interaction.id}',
                    'type': ['dit:Event', 'dit:Interaction'],
                    'startTime': format_date_or_datetime(interaction.date),
                    'dit:status': interaction.status,
                    'dit:archived': interaction.archived,
                    'dit:communicationChannel': {'name': interaction.communication_channel.name},
                    'dit:subject': interaction.subject,
                    'dit:service': {'name': interaction.service.name},
                    'attributedTo': [
                        {
                            'id': f'dit:DataHubCompany:{interaction.company.pk}',
                            'dit:dunsNumber': interaction.company.duns_number,
                            'dit:companiesHouseNumber': interaction.company.company_number,
                            'type': ['Organization', 'dit:Company'],
                            'name': interaction.company.name,
                        },
                        *[
                            {
                                'id': f'dit:DataHubAdviser:{participant.adviser.pk}',
                                'type': ['Person', 'dit:Adviser'],
                                'dit:emailAddress':
                                    participant.adviser.contact_email or participant.adviser.email,
                                'name': participant.adviser.name,
                            }
                            for participant in interaction.dit_participants.order_by('pk')
                        ],
                        *[
                            {
                                'id': f'dit:DataHubContact:{contact.pk}',
                                'type': ['Person', 'dit:Contact'],
                                'dit:emailAddress': contact.email,
                                'name': contact.name,
                            }
                            for contact in interaction.contacts.order_by('pk')
                        ],
                    ],
                    'url': interaction.get_absolute_url(),
                    'context': [
                        {
                            'id': f'dit:DataHubInvestmentProject:{project.pk}',
                            'name': project.name,
                            'type': 'dit:InvestmentProject',
                            'url': project.get_absolute_url(),
                        },
                    ],
                },
            },
        ],
    }


@pytest.mark.django_db
def test_service_delivery_activity(api_client):
    """
    Get a list of interactions and test the returned JSON is valid as per:
    https://www.w3.org/TR/activitystreams-core/
    """
    interaction = ServiceDeliveryFactory()
    response = _hawk_get(api_client, _url('api-v3:activity-stream:interactions'))
    assert response.status_code == status.HTTP_200_OK

    assert response.json() == {
        '@context': 'https://www.w3.org/ns/activitystreams',
        'summary': 'Interaction Activities',
        'type': 'OrderedCollectionPage',
        'id': 'http://testserver/v3/activity-stream/interactions',
        'partOf': 'http://testserver/v3/activity-stream/interactions',
        'previous': None,
        'next': None,
        'orderedItems': [
            {
                'id': f'dit:DataHubInteraction:{interaction.id}:Announce',
                'type': 'Announce',
                'published': format_date_or_datetime(interaction.created_on),
                'generator': {'name': 'dit:dataHub', 'type': 'Application'},
                'object': {
                    'id': f'dit:DataHubInteraction:{interaction.id}',
                    'type': ['dit:Event', 'dit:ServiceDelivery'],
                    'startTime': format_date_or_datetime(interaction.date),
                    'dit:status': interaction.status,
                    'dit:archived': interaction.archived,
                    'dit:subject': interaction.subject,
                    'dit:service': {'name': interaction.service.name},
                    'attributedTo': [
                        {
                            'id': f'dit:DataHubCompany:{interaction.company.pk}',
                            'dit:dunsNumber': interaction.company.duns_number,
                            'dit:companiesHouseNumber': interaction.company.company_number,
                            'type': ['Organization', 'dit:Company'],
                            'name': interaction.company.name,
                        },
                        *[
                            {
                                'id': f'dit:DataHubAdviser:{participant.adviser.pk}',
                                'type': ['Person', 'dit:Adviser'],
                                'dit:emailAddress':
                                    participant.adviser.contact_email or participant.adviser.email,
                                'name': participant.adviser.name,
                            }
                            for participant in interaction.dit_participants.order_by('pk')
                        ],
                        *[
                            {
                                'id': f'dit:DataHubContact:{contact.pk}',
                                'type': ['Person', 'dit:Contact'],
                                'dit:emailAddress': contact.email,
                                'name': contact.name,
                            }
                            for contact in interaction.contacts.order_by('pk')
                        ],
                    ],
                    'url': interaction.get_absolute_url(),
                },
            },
        ],
    }


@pytest.mark.django_db
def test_service_delivery_event_activity(api_client):
    """
    Get a list of interactions and test the returned JSON is valid as per:
    https://www.w3.org/TR/activitystreams-core/
    """
    interaction = EventServiceDeliveryFactory()
    event = interaction.event
    response = _hawk_get(api_client, _url('api-v3:activity-stream:interactions'))
    assert response.status_code == status.HTTP_200_OK

    assert response.json() == {
        '@context': 'https://www.w3.org/ns/activitystreams',
        'summary': 'Interaction Activities',
        'type': 'OrderedCollectionPage',
        'id': 'http://testserver/v3/activity-stream/interactions',
        'partOf': 'http://testserver/v3/activity-stream/interactions',
        'previous': None,
        'next': None,
        'orderedItems': [
            {
                'id': f'dit:DataHubInteraction:{interaction.id}:Announce',
                'type': 'Announce',
                'published': format_date_or_datetime(interaction.created_on),
                'generator': {'name': 'dit:dataHub', 'type': 'Application'},
                'object': {
                    'id': f'dit:DataHubInteraction:{interaction.id}',
                    'type': ['dit:Event', 'dit:ServiceDelivery'],
                    'startTime': format_date_or_datetime(interaction.date),
                    'dit:status': interaction.status,
                    'dit:archived': interaction.archived,
                    'dit:subject': interaction.subject,
                    'dit:service': {'name': interaction.service.name},
                    'attributedTo': [
                        {
                            'id': f'dit:DataHubCompany:{interaction.company.pk}',
                            'dit:dunsNumber': interaction.company.duns_number,
                            'dit:companiesHouseNumber': interaction.company.company_number,
                            'type': ['Organization', 'dit:Company'],
                            'name': interaction.company.name,
                        },
                        *[
                            {
                                'id': f'dit:DataHubAdviser:{participant.adviser.pk}',
                                'type': ['Person', 'dit:Adviser'],
                                'dit:emailAddress':
                                    participant.adviser.contact_email or participant.adviser.email,
                                'name': participant.adviser.name,
                            }
                            for participant in interaction.dit_participants.order_by('pk')
                        ],
                        *[
                            {
                                'id': f'dit:DataHubContact:{contact.pk}',
                                'type': ['Person', 'dit:Contact'],
                                'dit:emailAddress': contact.email,
                                'name': contact.name,
                            }
                            for contact in interaction.contacts.order_by('pk')
                        ],
                    ],
                    'url': interaction.get_absolute_url(),
                    'context': [
                        {
                            'id': f'dit:DataHubEvent:{event.pk}',
                            'type': 'dit:Event',
                            'dit:eventType': {'name': event.event_type.name},
                            'name': interaction.event.name,
                            'startTime': format_date_or_datetime(event.start_date),
                            'endTime': format_date_or_datetime(event.end_date),
                            'dit:team': {
                                'id': f'dit:DataHubTeam:{interaction.event.lead_team.pk}',
                                'type': ['Group', 'dit:Team'],
                                'name': interaction.event.lead_team.name,
                            },
                            'url': interaction.event.get_absolute_url(),
                        },
                    ],
                },
            },
        ],
    }


def test_kinds_mapping():
    """
    Tests if the mapping covers all kinds of interactions.
    """
    model_kinds = {k for k, _ in Interaction.KINDS}
    serializer_kinds = {k for k in InteractionActivitySerializer.KINDS_JSON}
    assert model_kinds == serializer_kinds


@pytest.mark.django_db
def test_interaction_ordering(api_client):
    """
    Test that the interactions are ordered by ('modified_on', 'pk')
    """
    interactions = []

    # We create 2 interactions with the same modified_on time
    with freeze_time():
        interactions += CompanyInteractionFactory.create_batch(2)
    interactions += CompanyInteractionFactory.create_batch(8)
    response = _hawk_get(api_client, _url('api-v3:activity-stream:interactions'))
    assert response.status_code == status.HTTP_200_OK

    sorted_interaction_ids = [
        f'dit:DataHubInteraction:{obj.pk}'
        for obj in sorted(interactions, key=lambda obj: (obj.modified_on, obj.pk))
    ]
    response_interaction_ids = [
        item['object']['id']
        for item in response.json()['orderedItems']
    ]
    assert sorted_interaction_ids == response_interaction_ids


@pytest.mark.django_db
def test_contacts_ordering(api_client):
    """
    Test that contacts are ordered by `pk`
    """
    contacts = ContactFactory.create_batch(5)
    CompanyInteractionFactory(contacts=contacts)
    response = _hawk_get(api_client, _url('api-v3:activity-stream:interactions'))
    assert response.status_code == status.HTTP_200_OK

    sorted_contact_ids = [
        f'dit:DataHubContact:{contact.pk}'
        for contact in sorted(contacts, key=lambda obj: obj.pk)
    ]
    items = response.json()['orderedItems'][0]['object']['attributedTo']
    response_contact_ids = [
        item['id']
        for item in items
        if item['type'] == ['Person', 'dit:Contact']
    ]
    assert sorted_contact_ids == response_contact_ids


@pytest.mark.django_db
def test_dit_participant_ordering(api_client):
    """
    Test that dit_participants are ordered by `pk`
    """
    interaction = CompanyInteractionFactory(dit_participants=[])
    InteractionDITParticipantFactory.create_batch(5, interaction=interaction)
    response = _hawk_get(api_client, _url('api-v3:activity-stream:interactions'))
    assert response.status_code == status.HTTP_200_OK

    sorted_participant_ids = [
        f'dit:DataHubAdviser:{participant.adviser.pk}'
        for participant in sorted(interaction.dit_participants.all(), key=lambda obj: obj.pk)
    ]
    items = response.json()['orderedItems'][0]['object']['attributedTo']
    response_participant_ids = [
        item['id']
        for item in items
        if item['type'] == ['Person', 'dit:Adviser']
    ]
    assert sorted_participant_ids == response_participant_ids


@pytest.mark.django_db
def test_cursor_pagination(api_client, monkeypatch):
    """
    Test if pagination behaves as expected
    """
    page_size = settings.REST_FRAMEWORK['PAGE_SIZE']
    interactions = CompanyInteractionFactory.create_batch(page_size + 1)
    response = _hawk_get(api_client, _url('api-v3:activity-stream:interactions'))
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    next_page_url = data['next']
    assert len(data['orderedItems']) == page_size

    response = _hawk_get(api_client, next_page_url)
    data = response.json()
    previous_page_url = data['previous']
    assert len(data['orderedItems']) == len(interactions) - page_size

    response = _hawk_get(api_client, previous_page_url)
    data = response.json()
    assert len(data['orderedItems']) == page_size
    assert data['next'] == next_page_url
