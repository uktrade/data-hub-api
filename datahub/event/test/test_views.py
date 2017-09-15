from operator import itemgetter

from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import AdviserFactory
from datahub.core.constants import Country, Team, UKRegion
from datahub.core.test_utils import APITestMixin
from datahub.event.constants import EventType, LocationType, Programme
from datahub.event.test.factories import EventFactory


class TestGetEventView(APITestMixin):
    """Get single event view tests."""

    def test_get(self):
        """Test getting a single event."""
        event = EventFactory()
        url = reverse('api-v3:event:item', kwargs={'pk': event.pk})

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        response_data = _get_canonical_response_data(response)
        expected_response_data = _canonicalise_response_data({
            'id': response_data['id'],
            'name': event.name,
            'event_type': {
                'id': str(event.event_type.id),
                'name': str(event.event_type.name),
            },
            'start_date': event.start_date,
            'end_date': event.end_date,
            'location_type': {
                'id': str(event.location_type.id),
                'name': event.location_type.name,
            },
            'notes': event.notes,
            'address_1': event.address_1,
            'address_2': event.address_2,
            'address_town': event.address_town,
            'address_county': event.address_county,
            'address_postcode': event.address_postcode,
            'address_country': {
                'id': str(event.address_country.id),
                'name': event.address_country.name,
            },
            'uk_region': {
                'id': UKRegion.east_of_england.value.id,
                'name': UKRegion.east_of_england.value.name,
            },
            'organiser': {
                'id': str(event.organiser.pk),
                'first_name': event.organiser.first_name,
                'last_name': event.organiser.last_name,
                'name': event.organiser.name,
            },
            'lead_team': {
                'id': str(event.lead_team.id),
                'name': event.lead_team.name,
            },
            'teams': [{
                'id': Team.healthcare_uk.value.id,
                'name': Team.healthcare_uk.value.name,
            }, {
                'id': Team.crm.value.id,
                'name': Team.crm.value.name,
            }],
            'related_programmes': [{
                'id': Programme.great_branded.value.id,
                'name': Programme.great_branded.value.name,
            }]
        })

        assert response_data == expected_response_data


class TestListEventView(APITestMixin):
    """List events view tests."""

    def test_list(self):
        """Tests listing events."""
        EventFactory.create_batch(2)
        url = reverse('api-v3:event:collection')

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()

        assert response_data['count'] == 2


class TestCreateEventView(APITestMixin):
    """Create event view tests."""

    def test_create_minimal_success(self):
        """Tests successfully creating an event with only the required fields."""
        url = reverse('api-v3:event:collection')
        request_data = {
            'name': 'Grand exhibition',
            'event_type': EventType.seminar.value.id,
            'address_1': 'Grand Court Exhibition Centre',
            'address_town': 'New York',
            'address_country': Country.united_states.value.id,
        }
        response = self.api_client.post(url, format='json', data=request_data)

        assert response.status_code == status.HTTP_201_CREATED
        response_data = _get_canonical_response_data(response)
        assert response_data == {
            'id': response_data['id'],
            'name': 'Grand exhibition',
            'event_type': {
                'id': EventType.seminar.value.id,
                'name': EventType.seminar.value.name,
            },
            'start_date': None,
            'end_date': None,
            'location_type': None,
            'notes': '',
            'address_1': 'Grand Court Exhibition Centre',
            'address_2': '',
            'address_town': 'New York',
            'address_county': '',
            'address_postcode': '',
            'address_country': {
                'id': Country.united_states.value.id,
                'name': Country.united_states.value.name,
            },
            'uk_region': None,
            'organiser': None,
            'lead_team': None,
            'teams': [],
            'related_programmes': []
        }

    def test_create_maximal_success(self):
        """Tests successfully creating an event with all fields completed."""
        url = reverse('api-v3:event:collection')
        request_data = {
            'name': 'Grand exhibition',
            'event_type': EventType.seminar.value.id,
            'start_date': '2020-01-01',
            'end_date': '2020-01-02',
            'location_type': LocationType.hq.value.id,
            'notes': 'Some notes',
            'address_1': 'Grand Court Exhibition Centre',
            'address_2': 'Grand Court Lane',
            'address_town': 'London',
            'address_county': 'Londinium',
            'address_postcode': 'SW9 9AA',
            'address_country': Country.united_kingdom.value.id,
            'uk_region': UKRegion.east_of_england.value.id,
            'organiser': str(self.user.pk),
            'lead_team': Team.crm.value.id,
            'teams': [Team.crm.value.id, Team.healthcare_uk.value.id],
            'related_programmes': [Programme.great_branded.value.id]
        }
        response = self.api_client.post(url, format='json', data=request_data)

        assert response.status_code == status.HTTP_201_CREATED
        response_data = _get_canonical_response_data(response)

        assert response_data == {
            'id': response_data['id'],
            'name': 'Grand exhibition',
            'event_type': {
                'id': EventType.seminar.value.id,
                'name': EventType.seminar.value.name,
            },
            'start_date': '2020-01-01',
            'end_date': '2020-01-02',
            'location_type': {
                'id': LocationType.hq.value.id,
                'name': LocationType.hq.value.name,
            },
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
            'uk_region': {
                'id': UKRegion.east_of_england.value.id,
                'name': UKRegion.east_of_england.value.name,
            },
            'organiser': {
                'id': str(self.user.pk),
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'name': self.user.name,
            },
            'lead_team': {
                'id': Team.crm.value.id,
                'name': Team.crm.value.name,
            },
            'teams': [{
                'id': Team.healthcare_uk.value.id,
                'name': Team.healthcare_uk.value.name,
            }, {
                'id': Team.crm.value.id,
                'name': Team.crm.value.name,
            }],
            'related_programmes': [{
                'id': Programme.great_branded.value.id,
                'name': Programme.great_branded.value.name,
            }]
        }

    def test_create_lead_team_not_in_teams(self):
        """Tests specifying a lead team that isn't in the teams array."""
        url = reverse('api-v3:event:collection')
        request_data = {
            'name': 'Grand exhibition',
            'event_type': EventType.seminar.value.id,
            'address_1': 'Grand Court Exhibition Centre',
            'address_town': 'London',
            'address_country': Country.united_kingdom.value.id,
            'uk_region': UKRegion.east_of_england.value.id,
            'lead_team': Team.crm.value.id,
            'teams': [Team.healthcare_uk.value.id],
        }
        response = self.api_client.post(url, format='json', data=request_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'lead_team': ['Lead team must be in teams array.']
        }

    def test_create_uk_no_uk_region(self):
        """Tests UK region requirement for UK events."""
        url = reverse('api-v3:event:collection')
        request_data = {
            'name': 'Grand exhibition',
            'event_type': EventType.seminar.value.id,
            'address_1': 'Grand Court Exhibition Centre',
            'address_town': 'London',
            'address_country': Country.united_kingdom.value.id,
        }
        response = self.api_client.post(url, format='json', data=request_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'uk_region': ['This field is required.']
        }

    def test_create_non_uk_with_uk_region(self):
        """Tests creating a non-UK event with a UK region."""
        url = reverse('api-v3:event:collection')
        request_data = {
            'name': 'Grand exhibition',
            'event_type': EventType.seminar.value.id,
            'address_1': 'Grand Court Exhibition Centre',
            'address_town': 'London',
            'address_country': Country.united_kingdom.value.id,
            'uk_region': UKRegion.east_of_england.value.id,
        }
        response = self.api_client.post(url, format='json', data=request_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'uk_region': ['Cannot specify a UK region for a non-UK country.']
        }

    def test_create_end_date_without_start_date(self):
        """Tests specifying an end date without a start date."""
        url = reverse('api-v3:event:collection')
        request_data = {
            'name': 'Grand exhibition',
            'event_type': EventType.seminar.value.id,
            'address_1': 'Grand Court Exhibition Centre',
            'address_town': 'London',
            'address_country': Country.united_kingdom.value.id,
            'uk_region': UKRegion.east_of_england.value.id,
            'end_date': '2020-01-01',
        }
        response = self.api_client.post(url, format='json', data=request_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'end_date': ['Cannot have an end date without a start date.']
        }

    def test_create_end_date_before_start_date(self):
        """Tests specifying an end date before the start date."""
        url = reverse('api-v3:event:collection')
        request_data = {
            'name': 'Grand exhibition',
            'event_type': EventType.seminar.value.id,
            'address_1': 'Grand Court Exhibition Centre',
            'address_town': 'London',
            'address_country': Country.united_kingdom.value.id,
            'uk_region': UKRegion.east_of_england.value.id,
            'start_date': '2020-01-02',
            'end_date': '2020-01-01',
        }
        response = self.api_client.post(url, format='json', data=request_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'end_date': ['End date cannot be before start date.']
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
            'event_type': None,
            'name': ''
        }
        response = self.api_client.post(url, format='json', data=request_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'address_1': ['This field may not be blank.'],
            'address_country': ['This field may not be null.'],
            'address_town': ['This field may not be blank.'],
            'event_type': ['This field may not be null.'],
            'name': ['This field may not be blank.']
        }


class TestUpdateEventView(APITestMixin):
    """Update event view tests."""

    def test_patch_all_fields(self):
        """Test updating an event."""
        event = EventFactory()
        organiser = AdviserFactory()
        url = reverse('api-v3:event:item', kwargs={'pk': event.pk})

        request_data = {
            'name': 'Annual exhibition',
            'event_type': EventType.exhibition.value.id,
            'start_date': '2021-01-01',
            'end_date': '2021-01-02',
            'location_type': LocationType.post.value.id,
            'notes': 'Updated notes',
            'address_1': 'Annual Court Exhibition Centre',
            'address_2': 'Annual Court Lane',
            'address_town': 'Annual',
            'address_county': 'County Annual',
            'address_postcode': 'SW9 9AB',
            'address_country': Country.isle_of_man.value.id,
            'uk_region': None,
            'organiser': str(organiser.pk),
            'lead_team': Team.food_from_britain.value.id,
            'teams': [Team.food_from_britain.value.id, Team.healthcare_uk.value.id],
            'related_programmes': [Programme.great_challenge_fund.value.id]
        }
        response = self.api_client.patch(url, request_data, format='json')
        assert response.status_code == status.HTTP_200_OK

        response_data = _get_canonical_response_data(response)

        assert response_data == {
            'id': str(event.pk),
            'name': 'Annual exhibition',
            'event_type': {
                'id': EventType.exhibition.value.id,
                'name': EventType.exhibition.value.name,
            },
            'start_date': '2021-01-01',
            'end_date': '2021-01-02',
            'location_type': {
                'id': LocationType.post.value.id,
                'name': LocationType.post.value.name,
            },
            'notes': 'Updated notes',
            'address_1': 'Annual Court Exhibition Centre',
            'address_2': 'Annual Court Lane',
            'address_town': 'Annual',
            'address_county': 'County Annual',
            'address_postcode': 'SW9 9AB',
            'address_country': {
                'id': Country.isle_of_man.value.id,
                'name': Country.isle_of_man.value.name,
            },
            'uk_region': None,
            'organiser': {
                'id': str(organiser.pk),
                'first_name': organiser.first_name,
                'last_name': organiser.last_name,
                'name': organiser.name,
            },
            'lead_team': {
                'id': Team.food_from_britain.value.id,
                'name': Team.food_from_britain.value.name,
            },
            'teams': [{
                'id': Team.healthcare_uk.value.id,
                'name': Team.healthcare_uk.value.name,
            }, {
                'id': Team.food_from_britain.value.id,
                'name': Team.food_from_britain.value.name,
            }],
            'related_programmes': [{
                'id': Programme.great_challenge_fund.value.id,
                'name': Programme.great_challenge_fund.value.name,
            }]
        }

    def test_patch_lead_team_success(self):
        """Test updating an event's lead team."""
        event = EventFactory()
        url = reverse('api-v3:event:item', kwargs={'pk': event.pk})

        request_data = {
            'lead_team': Team.healthcare_uk.value.id,
        }
        response = self.api_client.patch(url, request_data, format='json')
        assert response.status_code == status.HTTP_200_OK

        response_data = _get_canonical_response_data(response)
        assert response_data['lead_team']['id'] == Team.healthcare_uk.value.id

    def test_patch_lead_team_failure(self):
        """Test updating an event's lead team to an invalid team."""
        event = EventFactory()
        url = reverse('api-v3:event:item', kwargs={'pk': event.pk})

        request_data = {
            'lead_team': Team.food_from_britain.value.id,
        }
        response = self.api_client.patch(url, request_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        response_data = response.json()
        assert response_data == {
            'lead_team': ['Lead team must be in teams array.']
        }


def _get_canonical_response_data(response):
    return _canonicalise_response_data(response.json())


def _canonicalise_response_data(response_data):
    # The teams are returned in an undefined order, so we sort them here to allow
    # full comparisons
    response_data['teams'].sort(key=itemgetter('id'))
    response_data['related_programmes'].sort(key=itemgetter('id'))
    return response_data
