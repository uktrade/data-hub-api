import datetime

import pytest
from freezegun import freeze_time
from rest_framework import status

from datahub.activity_stream.interaction.serializers import InteractionActivitySerializer
from datahub.activity_stream.test import hawk
from datahub.activity_stream.test.utils import get_url
from datahub.core.constants import ExportBarrierType
from datahub.core.test.factories import to_many_field
from datahub.core.test_utils import format_date_or_datetime
from datahub.interaction.models import Interaction
from datahub.interaction.test.factories import (
    CompaniesInteractionFactory,
    ContactFactory,
    EventServiceDeliveryFactory,
    InteractionDITParticipantFactory,
    InvestmentProjectInteractionFactory,
    ServiceDeliveryFactory,
)
from datahub.metadata.test.factories import TeamFactory


class CompaniesInteractionWithExportBarrierOtherFactory(CompaniesInteractionFactory):
    """Create companies interaction with export barriers - Other."""

    helped_remove_export_barrier = True
    export_barrier_notes = 'Lorem ipsum'

    @to_many_field
    def export_barrier_types(self):
        """
        Add "other" export barrier type
        """
        return [ExportBarrierType.other.value.id]


class CompaniesInteractionWithExportBarrierFinanceFactory(CompaniesInteractionFactory):
    """Create companies interaction with export barriers - Finance."""

    helped_remove_export_barrier = True
    export_barrier_notes = ''

    @to_many_field
    def export_barrier_types(self):
        """
        Add "other" export barrier type
        """
        return [ExportBarrierType.finance.value.id]


@pytest.mark.django_db
@pytest.mark.parametrize(
    'factory',
    [
        CompaniesInteractionFactory,
        CompaniesInteractionWithExportBarrierOtherFactory,
        CompaniesInteractionWithExportBarrierFinanceFactory,
    ],
)
def test_interaction_activity(api_client, factory):
    """
    Get a list of interactions and test the returned JSON is valid as per:
    https://www.w3.org/TR/activitystreams-core/
    """
    start = datetime.datetime(year=2012, month=7, day=12, hour=15, minute=6, second=3)
    with freeze_time(start) as frozen_datetime:
        interaction = factory()
        frozen_datetime.tick(datetime.timedelta(seconds=1, microseconds=1))
        response = hawk.get(api_client, get_url('api-v3:activity-stream:interactions'))

    expected = {}
    if interaction.helped_remove_export_barrier:
        expected.update(
            {
                'dit:exportBarrierTypes': [
                    {'name': barrier.name for barrier in interaction.export_barrier_types.all()},
                ],
                **({'dit:exportBarrierNotes': interaction.export_barrier_notes}
                    if interaction.export_barrier_notes else {}),
            },
        )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        '@context': 'https://www.w3.org/ns/activitystreams',
        'summary': 'Interaction Activities',
        'type': 'OrderedCollectionPage',
        'next': 'http://testserver/v3/activity-stream/interaction'
                + '?cursor=2012-07-12T15%3A06%3A03.000000%2B00%3A00'
                + f'&cursor={str(interaction.id)}',
        'orderedItems': [
            {
                'id': f'dit:DataHubInteraction:{interaction.id}:Announce',
                'type': 'Announce',
                'published': format_date_or_datetime(interaction.created_on),
                'generator': {'name': 'dit:dataHub', 'type': 'Application'},
                'object': {
                    'id': f'dit:DataHubInteraction:{interaction.id}',
                    'type': [
                        'dit:Event',
                        'dit:Interaction',
                        f'dit:datahub:theme:{interaction.theme}',
                    ],
                    'content': interaction.notes,
                    'startTime': format_date_or_datetime(interaction.date),
                    'dit:status': interaction.status,
                    'dit:archived': interaction.archived,
                    'dit:communicationChannel': {'name': interaction.communication_channel.name},
                    'dit:subject': interaction.subject,
                    'dit:service': {'name': interaction.service.name},
                    'attributedTo': [
                        *[
                            {
                                'id': f'dit:DataHubCompany:{company.pk}',
                                'dit:dunsNumber': company.duns_number,
                                'dit:companiesHouseNumber': company.company_number,
                                'type': ['Organization', 'dit:Company'],
                                'name': company.name,
                            }
                            for company in interaction.companies.order_by('pk')
                        ],
                        *[
                            {
                                'id': f'dit:DataHubAdviser:{participant.adviser.pk}',
                                'type': ['Person', 'dit:Adviser'],
                                'dit:emailAddress':
                                    participant.adviser.contact_email or participant.adviser.email,
                                'name': participant.adviser.name,
                                'dit:team': {
                                    'id': f'dit:DataHubTeam:{participant.team.pk}',
                                    'type': ['Group', 'dit:Team'],
                                    'name': participant.team.name,
                                },
                            }
                            for participant in interaction.dit_participants.order_by('pk')
                        ],
                        *[
                            {
                                'id': f'dit:DataHubContact:{contact.pk}',
                                'type': ['Person', 'dit:Contact'],
                                'url': contact.get_absolute_url(),
                                'dit:emailAddress': contact.email,
                                'dit:jobTitle': contact.job_title,
                                'name': contact.name,
                            }
                            for contact in interaction.contacts.order_by('pk')
                        ],
                    ],
                    'url': interaction.get_absolute_url(),
                    **expected,
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
    start = datetime.datetime(year=2012, month=7, day=12, hour=15, minute=6, second=3)
    with freeze_time(start) as frozen_datetime:
        interaction = InvestmentProjectInteractionFactory()
        project = interaction.investment_project
        frozen_datetime.tick(datetime.timedelta(seconds=1, microseconds=1))
        response = hawk.get(api_client, get_url('api-v3:activity-stream:interactions'))

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        '@context': 'https://www.w3.org/ns/activitystreams',
        'summary': 'Interaction Activities',
        'type': 'OrderedCollectionPage',
        'next': 'http://testserver/v3/activity-stream/interaction'
                + '?cursor=2012-07-12T15%3A06%3A03.000000%2B00%3A00'
                + f'&cursor={str(interaction.id)}',
        'orderedItems': [
            {
                'id': f'dit:DataHubInteraction:{interaction.id}:Announce',
                'type': 'Announce',
                'published': format_date_or_datetime(interaction.created_on),
                'generator': {'name': 'dit:dataHub', 'type': 'Application'},
                'object': {
                    'id': f'dit:DataHubInteraction:{interaction.id}',
                    'type': [
                        'dit:Event',
                        'dit:Interaction',
                        f'dit:datahub:theme:{interaction.theme}',
                    ],
                    'content': interaction.notes,
                    'startTime': format_date_or_datetime(interaction.date),
                    'dit:status': interaction.status,
                    'dit:archived': interaction.archived,
                    'dit:communicationChannel': {'name': interaction.communication_channel.name},
                    'dit:subject': interaction.subject,
                    'dit:service': {'name': interaction.service.name},
                    'attributedTo': [
                        *[
                            {
                                'id': f'dit:DataHubCompany:{company.pk}',
                                'dit:dunsNumber': company.duns_number,
                                'dit:companiesHouseNumber': company.company_number,
                                'type': ['Organization', 'dit:Company'],
                                'name': company.name,
                            }
                            for company in interaction.companies.order_by('pk')
                        ],
                        *[
                            {
                                'id': f'dit:DataHubAdviser:{participant.adviser.pk}',
                                'type': ['Person', 'dit:Adviser'],
                                'dit:emailAddress':
                                    participant.adviser.contact_email or participant.adviser.email,
                                'name': participant.adviser.name,
                                'dit:team': {
                                    'id': f'dit:DataHubTeam:{participant.team.pk}',
                                    'type': ['Group', 'dit:Team'],
                                    'name': participant.team.name,
                                },
                            }
                            for participant in interaction.dit_participants.order_by('pk')
                        ],
                        *[
                            {
                                'id': f'dit:DataHubContact:{contact.pk}',
                                'type': ['Person', 'dit:Contact'],
                                'url': contact.get_absolute_url(),
                                'dit:emailAddress': contact.email,
                                'dit:jobTitle': contact.job_title,
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
    start = datetime.datetime(year=2012, month=7, day=12, hour=15, minute=6, second=3)
    with freeze_time(start) as frozen_datetime:
        interaction = ServiceDeliveryFactory()
        frozen_datetime.tick(datetime.timedelta(seconds=1, microseconds=1))
        response = hawk.get(api_client, get_url('api-v3:activity-stream:interactions'))

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        '@context': 'https://www.w3.org/ns/activitystreams',
        'summary': 'Interaction Activities',
        'type': 'OrderedCollectionPage',
        'next': 'http://testserver/v3/activity-stream/interaction'
                + '?cursor=2012-07-12T15%3A06%3A03.000000%2B00%3A00'
                + f'&cursor={str(interaction.id)}',
        'orderedItems': [
            {
                'id': f'dit:DataHubInteraction:{interaction.id}:Announce',
                'type': 'Announce',
                'published': format_date_or_datetime(interaction.created_on),
                'generator': {'name': 'dit:dataHub', 'type': 'Application'},
                'object': {
                    'id': f'dit:DataHubInteraction:{interaction.id}',
                    'type': [
                        'dit:Event',
                        'dit:ServiceDelivery',
                        f'dit:datahub:theme:{interaction.theme}',
                    ],
                    'content': interaction.notes,
                    'startTime': format_date_or_datetime(interaction.date),
                    'dit:status': interaction.status,
                    'dit:archived': interaction.archived,
                    'dit:subject': interaction.subject,
                    'dit:service': {'name': interaction.service.name},
                    'attributedTo': [
                        *[
                            {
                                'id': f'dit:DataHubCompany:{company.pk}',
                                'dit:dunsNumber': company.duns_number,
                                'dit:companiesHouseNumber': company.company_number,
                                'type': ['Organization', 'dit:Company'],
                                'name': company.name,
                            }
                            for company in interaction.companies.order_by('pk')
                        ],
                        *[
                            {
                                'id': f'dit:DataHubAdviser:{participant.adviser.pk}',
                                'type': ['Person', 'dit:Adviser'],
                                'dit:emailAddress':
                                    participant.adviser.contact_email or participant.adviser.email,
                                'name': participant.adviser.name,
                                'dit:team': {
                                    'id': f'dit:DataHubTeam:{participant.team.pk}',
                                    'type': ['Group', 'dit:Team'],
                                    'name': participant.team.name,
                                },
                            }
                            for participant in interaction.dit_participants.order_by('pk')
                        ],
                        *[
                            {
                                'id': f'dit:DataHubContact:{contact.pk}',
                                'type': ['Person', 'dit:Contact'],
                                'url': contact.get_absolute_url(),
                                'dit:emailAddress': contact.email,
                                'dit:jobTitle': contact.job_title,
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
    start = datetime.datetime(year=2012, month=7, day=12, hour=15, minute=6, second=3)
    with freeze_time(start) as frozen_datetime:
        interaction = EventServiceDeliveryFactory()
        event = interaction.event
        frozen_datetime.tick(datetime.timedelta(seconds=1, microseconds=1))
        response = hawk.get(api_client, get_url('api-v3:activity-stream:interactions'))

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        '@context': 'https://www.w3.org/ns/activitystreams',
        'summary': 'Interaction Activities',
        'type': 'OrderedCollectionPage',
        'next': 'http://testserver/v3/activity-stream/interaction'
                + '?cursor=2012-07-12T15%3A06%3A03.000000%2B00%3A00'
                + f'&cursor={str(interaction.id)}',
        'orderedItems': [
            {
                'id': f'dit:DataHubInteraction:{interaction.id}:Announce',
                'type': 'Announce',
                'published': format_date_or_datetime(interaction.created_on),
                'generator': {'name': 'dit:dataHub', 'type': 'Application'},
                'object': {
                    'id': f'dit:DataHubInteraction:{interaction.id}',
                    'type': [
                        'dit:Event',
                        'dit:ServiceDelivery',
                        f'dit:datahub:theme:{interaction.theme}',
                    ],
                    'content': interaction.notes,
                    'startTime': format_date_or_datetime(interaction.date),
                    'dit:status': interaction.status,
                    'dit:archived': interaction.archived,
                    'dit:subject': interaction.subject,
                    'dit:service': {'name': interaction.service.name},
                    'attributedTo': [
                        *[
                            {
                                'id': f'dit:DataHubCompany:{company.pk}',
                                'dit:dunsNumber': company.duns_number,
                                'dit:companiesHouseNumber': company.company_number,
                                'type': ['Organization', 'dit:Company'],
                                'name': company.name,
                            }
                            for company in interaction.companies.order_by('pk')
                        ],
                        *[
                            {
                                'id': f'dit:DataHubAdviser:{participant.adviser.pk}',
                                'type': ['Person', 'dit:Adviser'],
                                'dit:emailAddress':
                                    participant.adviser.contact_email or participant.adviser.email,
                                'name': participant.adviser.name,
                                'dit:team': {
                                    'id': f'dit:DataHubTeam:{participant.team.pk}',
                                    'type': ['Group', 'dit:Team'],
                                    'name': participant.team.name,
                                },
                            }
                            for participant in interaction.dit_participants.order_by('pk')
                        ],
                        *[
                            {
                                'id': f'dit:DataHubContact:{contact.pk}',
                                'type': ['Person', 'dit:Contact'],
                                'url': contact.get_absolute_url(),
                                'dit:emailAddress': contact.email,
                                'dit:jobTitle': contact.job_title,
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
    model_kinds = set(Interaction.Kind.values)
    serializer_kinds = {k for k in InteractionActivitySerializer.KINDS_JSON}
    assert model_kinds == serializer_kinds


@pytest.mark.django_db
def test_interaction_ordering(api_client):
    """
    Test that the interactions are ordered by ('modified_on', 'pk')
    """
    interactions = []

    with freeze_time() as frozen_datetime:
        interactions += CompaniesInteractionFactory.create_batch(2)

        frozen_datetime.tick(datetime.timedelta(microseconds=1))
        interactions += CompaniesInteractionFactory.create_batch(8)

        frozen_datetime.tick(datetime.timedelta(seconds=1, microseconds=1))
        response = hawk.get(api_client, get_url('api-v3:activity-stream:interactions'))

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
    with freeze_time() as frozen_datetime:
        contacts = ContactFactory.create_batch(5)
        CompaniesInteractionFactory(contacts=contacts)

        frozen_datetime.tick(datetime.timedelta(seconds=1, microseconds=1))
        response = hawk.get(api_client, get_url('api-v3:activity-stream:interactions'))

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
    with freeze_time() as frozen_datetime:
        interaction = CompaniesInteractionFactory(dit_participants=[])
        InteractionDITParticipantFactory.create_batch(5, interaction=interaction)

        frozen_datetime.tick(datetime.timedelta(seconds=1, microseconds=1))
        response = hawk.get(api_client, get_url('api-v3:activity-stream:interactions'))

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
def test_null_adviser(api_client):
    """
    Test that we can handle dit_participant.adviser being None
    """
    with freeze_time() as frozen_datetime:
        interaction = CompaniesInteractionFactory(dit_participants=[])
        InteractionDITParticipantFactory(
            interaction=interaction,
            adviser=None,
            team=TeamFactory(),
        )

        frozen_datetime.tick(datetime.timedelta(seconds=1, microseconds=1))
        response = hawk.get(api_client, get_url('api-v3:activity-stream:interactions'))
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_null_team(api_client):
    """
    Test that we can handle dit_participant.team being None
    """
    interaction = EventServiceDeliveryFactory(dit_participants=[])
    InteractionDITParticipantFactory(
        interaction=interaction,
        team=None,
    )
    response = hawk.get(api_client, get_url('api-v3:activity-stream:interactions'))
    assert response.status_code == status.HTTP_200_OK
