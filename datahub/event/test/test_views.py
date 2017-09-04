from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.constants import Country, Team
from datahub.core.test_utils import APITestMixin
from datahub.event.constants import Programme
from datahub.event.models import Event


class TestEventViews(APITestMixin):
    """Event view tests."""

    def test_create_minimal_success(self):
        """Tests successfully creating an event with only the required fields."""
        url = reverse('api-v3:event:collection')
        request_data = {
            'name': 'Grand exhibition',
            'event_type': 'Seminar',
            'address_1': 'Grand Court Exhibition Centre',
            'address_town': 'London',
            'address_country': Country.united_kingdom.value.id,
        }
        response = self.api_client.post(url, format='json', data=request_data)

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data == {
            'id': response_data['id'],
            'name': 'Grand exhibition',
            'event_type': 'Seminar',
            'start_date': None,
            'end_date': None,
            'location_type': '',
            'notes': '',
            'address_1': 'Grand Court Exhibition Centre',
            'address_2': '',
            'address_town': 'London',
            'address_county': '',
            'address_postcode': '',
            'address_country': {
                'id': Country.united_kingdom.value.id,
                'name': Country.united_kingdom.value.name,
            },
            'lead_team': None,
            'additional_teams': [],
            'related_programmes': []
        }

    def test_create_maximal_success(self):
        """Tests successfully creating an event with all fields completed."""
        url = reverse('api-v3:event:collection')
        request_data = {
            'name': 'Grand exhibition',
            'event_type': Event.EVENT_TYPES.seminar,
            'start_date': '2020-01-01',
            'end_date': '2020-01-02',
            'location_type': Event.LOCATION_TYPES.hq,
            'notes': 'Some notes',
            'address_1': 'Grand Court Exhibition Centre',
            'address_2': 'Grand Court Lane',
            'address_town': 'London',
            'address_county': 'Londinium',
            'address_postcode': 'SW9 9AA',
            'address_country': Country.united_kingdom.value.id,
            'lead_team': Team.crm.value.id,
            'additional_teams': [Team.healthcare_uk.value.id],
            'related_programmes': [Programme.great_branded.value.id]
        }
        response = self.api_client.post(url, format='json', data=request_data)

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data == {
            'id': response_data['id'],
            'name': 'Grand exhibition',
            'event_type': Event.EVENT_TYPES.seminar,
            'start_date': '2020-01-01',
            'end_date': '2020-01-02',
            'location_type': Event.LOCATION_TYPES.hq,
            'notes': 'Some notes',
            'address_1': 'Grand Court Exhibition Centre',
            'address_2': 'Grand Court Lane',
            'address_town': 'London',
            'address_county': 'Londinium',
            'address_postcode': 'SW9 9AA',
            'address_country': {
                'id': Country.united_kingdom.value.id,
                'name': Country.united_kingdom.value.name,
            },
            'lead_team': {
                'id': Team.crm.value.id,
                'name': Team.crm.value.name,
            },
            'additional_teams': [{
                'id': Team.healthcare_uk.value.id,
                'name': Team.healthcare_uk.value.name,
            }],
            'related_programmes': [{
                'id': Programme.great_branded.value.id,
                'name': Programme.great_branded.value.name,
            }]
        }

    def test_create_omitted_failure(self):
        """Tests creating an event without required fields."""
        url = reverse('api-v3:event:collection')
        request_data = {}
        response = self.api_client.post(url, format='json', data=request_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'address_1': ['This field is required.'],
            'address_country': ['This field is required.'],
            'address_town': ['This field is required.'],
            'event_type': ['This field is required.'],
            'name': ['This field is required.']
        }

    def test_create_blank_failure(self):
        """Tests creating an event with blank required fields."""
        url = reverse('api-v3:event:collection')
        request_data = {
            'address_1': '',
            'address_country': None,
            'address_town': '',
            'event_type': '',
            'name': ''
        }
        response = self.api_client.post(url, format='json', data=request_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'address_1': ['This field may not be blank.'],
            'address_country': ['This field may not be null.'],
            'address_town': ['This field may not be blank.'],
            'event_type': ['"" is not a valid choice.'],
            'name': ['This field may not be blank.']
        }
