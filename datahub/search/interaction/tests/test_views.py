from collections import Counter

import pytest
from django.utils.crypto import get_random_string
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory
from datahub.core import constants
from datahub.core.test_utils import APITestMixin
from datahub.interaction.models import Interaction
from datahub.interaction.test.factories import InteractionFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def interactions(setup_es):
    """Sets up data for the tests."""
    data = []
    with freeze_time('2017-01-01 13:00:00'):
        data.extend([
            InteractionFactory(subject='Exports meeting'),
            InteractionFactory(subject='A coffee'),
            InteractionFactory(subject='Email about exhibition'),
            InteractionFactory(subject='Talking about cats'),
            InteractionFactory(subject='Event at HQ'),
        ])

    setup_es.indices.refresh()

    yield data


@pytest.mark.usefixtures('interactions')
class TestViews(APITestMixin):
    """Tests interaction search views."""

    def test_get_all(self, interactions):
        """
        Tests that all interactions are returned with an empty POST body.
        """
        url = reverse('api-v3:search:interaction')

        response = self.api_client.post(url, {}, format='json')

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == len(interactions)
        expected_ids = Counter(str(interaction.id) for interaction in interactions)
        assert Counter([item['id'] for item in response_data['results']]) == expected_ids

    def test_limit(self):
        """Tests that results can be limited."""
        url = reverse('api-v3:search:interaction')

        request_data = {
            'limit': 1
        }
        response = self.api_client.post(url, request_data, format='json')

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert len(response_data['results']) == 1

    def test_offset(self):
        """Tests that results can be offset."""
        url = reverse('api-v3:search:interaction')

        request_data = {
            'offset': 1
        }
        response = self.api_client.post(url, request_data, format='json')

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert len(response_data['results']) == 4

    def test_sort_by_subject_asc(self, interactions):
        """Tests sorting of results by subject (ascending)."""
        url = reverse('api-v3:search:interaction')

        request_data = {
            'sortby': 'subject:asc'
        }
        response = self.api_client.post(url, request_data, format='json')

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == len(interactions)
        expected_subjects = list(sorted(interaction.subject for interaction in interactions))
        assert [item['subject'] for item in response_data['results']] == expected_subjects

    def test_sort_by_subject_desc(self, interactions):
        """Tests sorting of results by subject (ascending)."""
        url = reverse('api-v3:search:interaction')

        request_data = {
            'sortby': 'subject:desc'
        }
        response = self.api_client.post(url, request_data, format='json')

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == len(interactions)
        expected_subjects = list(sorted((interaction.subject for interaction in interactions),
                                        reverse=True))
        assert [item['subject'] for item in response_data['results']] == expected_subjects

    def test_sort_by_invalid_field(self):
        """Tests attempting to sort by an invalid field and direction."""
        url = reverse('api-v3:search:interaction')

        request_data = {
            'sortby': 'gyratory:backwards'
        }
        response = self.api_client.post(url, request_data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'sortby': [
                "'sortby' field is not one of ('company.name', 'contact.name', 'date'"
                ", 'dit_adviser.name', 'dit_team.name', 'id', 'subject').",
                "Invalid sort direction 'backwards', must be one of ('asc', 'desc')",
            ]
        }

    @pytest.mark.parametrize('term', ('exports', 'meeting', 'exports meeting'))
    def test_search_original_query(self, interactions, term):
        """Tests searching across fields for a particular interaction."""
        url = reverse('api-v3:search:interaction')

        request_data = {
            'original_query': term
        }
        response = self.api_client.post(url, request_data, format='json')

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        interaction = interactions[0]
        assert response_data['count'] == 1
        assert response_data['results'] == [{
            'id': str(interaction.pk),
            'kind': interaction.kind,
            'date': interaction.date.isoformat(),
            'company': {
                'id': str(interaction.company.pk),
                'name': interaction.company.name,
            },
            'contact': {
                'id': str(interaction.contact.pk),
                'first_name': interaction.contact.first_name,
                'name': interaction.contact.name,
                'last_name': interaction.contact.last_name,
            },
            'event': None,
            'service': {
                'id': str(interaction.service.pk),
                'name': interaction.service.name,
            },
            'subject': interaction.subject,
            'dit_adviser': {
                'id': str(interaction.dit_adviser.pk),
                'first_name': interaction.dit_adviser.first_name,
                'name': interaction.dit_adviser.name,
                'last_name': interaction.dit_adviser.last_name,
            },
            'notes': interaction.notes,
            'dit_team': {
                'id': str(interaction.dit_team.pk),
                'name': interaction.dit_team.name,
            },
            'communication_channel': {
                'id': str(interaction.communication_channel.pk),
                'name': interaction.communication_channel.name,
            },
            'investment_project': None,
            'created_on': interaction.created_on.isoformat(),
            'modified_on': interaction.modified_on.isoformat(),
        }]

    def test_filter_by_kind(self, setup_es):
        """Tests filtering interaction by kind."""
        service_deliveries = []

        for _ in range(10):
            InteractionFactory(
                kind=Interaction.KINDS.interaction,
            )
            service_deliveries.append(InteractionFactory(
                kind=Interaction.KINDS.service_delivery,
            ))
        setup_es.indices.refresh()

        url = reverse('api-v3:search:interaction')
        request_data = {
            'kind': Interaction.KINDS.service_delivery,
        }
        response = self.api_client.post(url, request_data, format='json')

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert response_data['count'] == 10

        results = response_data['results']
        service_delivery_ids = {str(interaction.id) for interaction in service_deliveries}
        assert {result['id'] for result in results} == service_delivery_ids

    def test_filter_by_company_id(self, setup_es):
        """Tests filtering interaction by company id."""
        companies = CompanyFactory.create_batch(10)
        for company in companies:
            InteractionFactory(
                company=company
            )
        setup_es.indices.refresh()

        url = reverse('api-v3:search:interaction')
        request_data = {
            'company': companies[5].id
        }
        response = self.api_client.post(url, request_data, format='json')

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert response_data['count'] == 1

        results = response_data['results']
        assert results[0]['company']['id'] == str(companies[5].id)

    def test_filter_by_company_name(self, setup_es):
        """Tests filtering interaction by company name."""
        companies = []
        for i in range(10):
            companies.append(CompanyFactory(name=get_random_string(16)))
            InteractionFactory(company=companies[i])

        setup_es.indices.refresh()

        url = reverse('api-v3:search:interaction')
        request_data = {
            'company_name': companies[5].name
        }
        response = self.api_client.post(url, request_data, format='json')

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert response_data['count'] > 0

        results = response_data['results']
        # multiple records can match our filter, let's make sure at least one is exact match
        assert any(result['company']['id'] == str(companies[5].id) for result in results)
        assert any(result['company']['name'] == companies[5].name for result in results)

    def test_filter_by_contact_id(self, setup_es):
        """Tests filtering interaction by contact id."""
        contacts = ContactFactory.create_batch(10)
        for contact in contacts:
            InteractionFactory(
                contact=contact
            )
        setup_es.indices.refresh()

        url = reverse('api-v3:search:interaction')
        request_data = {
            'contact': contacts[5].id
        }
        response = self.api_client.post(url, request_data, format='json')

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert response_data['count'] == 1

        results = response_data['results']
        assert results[0]['contact']['id'] == str(contacts[5].id)

    def test_filter_by_contact_name(self, setup_es):
        """Tests filtering interaction by contact name."""
        contacts = []
        for i in range(10):
            contacts.append(ContactFactory(
                first_name=get_random_string(16),
                last_name=get_random_string(16),
            ))
            InteractionFactory(
                contact=contacts[i]
            )
        setup_es.indices.refresh()

        url = reverse('api-v3:search:interaction')
        request_data = {
            'contact_name': contacts[5].name
        }
        response = self.api_client.post(url, request_data, format='json')

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert response_data['count'] > 0

        results = response_data['results']
        # multiple records can match our filter, let's make sure at least one is exact match
        assert any(result['contact']['id'] == str(contacts[5].id) for result in results)
        assert any(result['contact']['name'] == contacts[5].name for result in results)

    def test_filter_by_dit_adviser_name(self, setup_es):
        """Tests filtering interaction by dit adviser name."""
        advisers = []
        for i in range(10):
            advisers.append(AdviserFactory(
                first_name=get_random_string(16),
                last_name=get_random_string(16),
            ))
            InteractionFactory(
                dit_adviser=advisers[i]
            )
        setup_es.indices.refresh()

        url = reverse('api-v3:search:interaction')
        request_data = {
            'dit_adviser_name': advisers[5].name
        }
        response = self.api_client.post(url, request_data, format='json')

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert response_data['count'] > 0

        results = response_data['results']
        # multiple records can match our filter, let's make sure at least one is exact match
        assert any(result['dit_adviser']['id'] == str(advisers[5].id) for result in results)
        assert any(result['dit_adviser']['name'] == advisers[5].name for result in results)

    def test_filter_by_dit_team(self, setup_es):
        """Tests filtering interaction by dit team."""
        dit_team_id = constants.Team.td_events_healthcare.value.id
        for _ in range(5):
            InteractionFactory(dit_team_id=constants.Team.crm.value.id)
            InteractionFactory(
                dit_team_id=dit_team_id
            )
        setup_es.indices.refresh()

        url = reverse('api-v3:search:interaction')
        request_data = {
            'dit_team': dit_team_id
        }
        response = self.api_client.post(url, request_data, format='json')

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert response_data['count'] == 5

        results = response_data['results']
        assert {result['dit_team']['id'] for result in results} == {str(dit_team_id)}

    def test_filter_by_communication_channel(self, setup_es):
        """Tests filtering interaction by interaction type."""
        communication_channel_id = constants.InteractionType.social_media.value.id
        for _ in range(5):
            InteractionFactory(
                communication_channel_id=constants.InteractionType.email_website.value.id
            )
            InteractionFactory(
                communication_channel_id=communication_channel_id
            )
        setup_es.indices.refresh()

        url = reverse('api-v3:search:interaction')
        request_data = {
            'original_query': '',
            'communication_channel': communication_channel_id
        }
        response = self.api_client.post(url, request_data, format='json')

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert response_data['count'] == 5

        results = response_data['results']
        result_ids = {result['communication_channel']['id'] for result in results}
        assert result_ids == {str(communication_channel_id)}

    def test_filter_by_service(self, setup_es):
        """Tests filtering interaction by service."""
        service_id = constants.Service.account_management.value.id
        for _ in range(5):
            InteractionFactory(
                service_id=constants.Service.trade_enquiry.value.id
            )
            InteractionFactory(
                service_id=service_id
            )
        setup_es.indices.refresh()

        url = reverse('api-v3:search:interaction')
        request_data = {
            'service': service_id
        }
        response = self.api_client.post(url, request_data, format='json')

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert response_data['count'] == 5

        results = response_data['results']
        result_ids = {result['service']['id'] for result in results}
        assert result_ids == {str(service_id)}
