import datetime

import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import AdviserFactory
from datahub.core import constants
from datahub.core.test_utils import APITestMixin
from datahub.event.test.factories import EventFactory
from datahub.metadata.test.factories import TeamFactory


@pytest.fixture
def setup_data():
    """Sets up data for the tests."""
    EventFactory.create_batch(2)


pytestmark = pytest.mark.django_db


class TestSearch(APITestMixin):
    """Tests search views."""

    def test_search_event(self, setup_es, setup_data):
        """Tests detailed event search."""
        event_name = '012345catsinspace'
        EventFactory(
            name=event_name
        )
        setup_es.indices.refresh()

        url = reverse('api-v3:search:event')

        response = self.api_client.post(url, {
            'original_query': event_name,
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == event_name

    def test_event_search_paging(self, setup_es, setup_data):
        """Tests pagination of results."""
        setup_es.indices.refresh()

        url = reverse('api-v3:search:event')
        response = self.api_client.post(url, {
            'offset': 1,
            'limit': 1,
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] > 1
        assert len(response.data['results']) == 1

    def test_search_event_no_filters(self, setup_es, setup_data):
        """Tests case where there is no filters provided."""
        setup_es.indices.refresh()

        url = reverse('api-v3:search:event')
        response = self.api_client.post(url, {})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) > 0

    def test_search_event_name(self, setup_es, setup_data):
        """Tests event_name filter."""
        event_name = '0000000000'
        EventFactory(
            name=event_name
        )
        setup_es.indices.refresh()

        url = reverse('api-v3:search:event')

        response = self.api_client.post(url, {
            'name': event_name[:5],
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == event_name

    def test_search_event_organiser(self, setup_es, setup_data):
        """Tests organiser filter."""
        organiser = AdviserFactory()
        EventFactory(
            organiser=organiser
        )
        setup_es.indices.refresh()

        url = reverse('api-v3:search:event')

        response = self.api_client.post(url, {
            'organiser': organiser.id,
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['organiser']['id'] == str(organiser.id)

    def test_search_event_organiser_name(self, setup_es, setup_data):
        """Tests organiser_name filter."""
        organiser_name = '00000000 000000000'
        EventFactory(
            organiser=AdviserFactory(
                first_name=organiser_name.split(' ', maxsplit=1)[0],
                last_name=organiser_name.split(' ', maxsplit=1)[1],
            )
        )
        setup_es.indices.refresh()

        url = reverse('api-v3:search:event')

        response = self.api_client.post(url, {
            'organiser_name': '00000',
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['organiser']['name'] == organiser_name

    def test_search_event_address_country(self, setup_es, setup_data):
        """Tests address_country filter."""
        country_id = constants.Country.united_states.value.id
        EventFactory(
            address_country_id=country_id,
        )
        setup_es.indices.refresh()

        url = reverse('api-v3:search:event')

        response = self.api_client.post(url, {
            'address_country': country_id,
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['address_country']['id'] == country_id

    def test_search_event_lead_team(self, setup_es):
        """Tests lead_team filter."""
        url = reverse('api-v3:search:event')

        team = TeamFactory()
        EventFactory.create_batch(5)
        EventFactory.create_batch(5, lead_team_id=team.id)
        setup_es.indices.refresh()

        response = self.api_client.post(url, {
            'lead_team': team.id,
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 5
        assert len(response.data['results']) == 5

        team_ids = [result['lead_team']['id'] for result in response.data['results']]

        assert all(team_id == str(team.id) for team_id in team_ids)

    def test_search_event_teams(self, setup_es):
        """Tests teams filter."""
        url = reverse('api-v3:search:event')

        team_a = TeamFactory()
        team_b = TeamFactory()
        team_c = TeamFactory()
        EventFactory(teams=(team_c,))
        EventFactory.create_batch(5, teams=(team_a, team_b,))
        EventFactory.create_batch(5, teams=(team_b,))

        setup_es.indices.refresh()

        response = self.api_client.post(url, {
            'teams': (team_a.id, team_c.id,)
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        print(response.data['results'])
        assert response.data['count'] == 6
        assert len(response.data['results']) == 6

        event_teams = (result['teams'] for result in response.data['results'])
        for teams in event_teams:
            team_ids = {team['id'] for team in teams}
            assert len(team_ids.intersection({str(team_a.id), str(team_c.id)})) > 0

    def test_search_event_disabled_on(self, setup_es):
        """Tests disabled_on filter."""
        url = reverse('api-v3:search:event')

        current_datetime = datetime.datetime.utcnow()
        EventFactory.create_batch(5)
        EventFactory.create_batch(5, disabled_on=current_datetime)

        setup_es.indices.refresh()

        response = self.api_client.post(url, {
            'disabled_on_after': current_datetime,
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 5
        assert len(response.data['results']) == 5

        disabled_ons = [result['disabled_on'] for result in response.data['results']]
        assert all(disabled_on == current_datetime.isoformat() for disabled_on in disabled_ons)

    def test_search_event_disabled_on_doesnt_exist(self, setup_es):
        """Tests disabled_on is null filter."""
        url = reverse('api-v3:search:event')

        current_datetime = datetime.datetime.utcnow()
        EventFactory.create_batch(5)
        EventFactory.create_batch(5, disabled_on=current_datetime)

        setup_es.indices.refresh()

        response = self.api_client.post(url, {
            'disabled_on_exists': False,
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 5
        assert len(response.data['results']) == 5

        disabled_ons = (result['disabled_on'] for result in response.data['results'])
        assert all(disabled_on is None for disabled_on in disabled_ons)

    def test_search_event_disabled_on_exists(self, setup_es):
        """Tests disabled_on is null filter."""
        url = reverse('api-v3:search:event')

        current_datetime = datetime.datetime.utcnow()
        EventFactory.create_batch(5)
        EventFactory.create_batch(5, disabled_on=current_datetime)

        setup_es.indices.refresh()

        response = self.api_client.post(url, {
            'disabled_on_exists': True,
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        # We should get at least 5 disabled events, as some already exist
        assert response.data['count'] == 5
        assert len(response.data['results']) == 5

        disabled_ons = (result['disabled_on'] for result in response.data['results'])
        assert all(disabled_on is not None for disabled_on in disabled_ons)

    def test_search_event_uk_region(self, setup_es):
        """Tests uk_region filter."""
        country_id = constants.Country.united_kingdom.value.id
        uk_region_id = constants.UKRegion.jersey.value.id
        EventFactory(
            address_country_id=country_id,
            uk_region_id=uk_region_id,
        )
        setup_es.indices.refresh()

        url = reverse('api-v3:search:event')

        response = self.api_client.post(url, {
            'uk_region': uk_region_id,
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['address_country']['id'] == country_id
        assert response.data['results'][0]['uk_region']['id'] == uk_region_id

    def test_search_event_date(self, setup_es, setup_data):
        """Tests start_date filter."""
        start_date = datetime.date(2017, 7, 2)
        event = EventFactory(
            start_date=start_date,
        )
        setup_es.indices.refresh()

        url = reverse('api-v3:search:event')

        response = self.api_client.post(url, {
            'original_query': '',
            'start_date_after': start_date,
            'start_date_before': start_date,
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['id'] == str(event.id)

    def test_search_event_sortby_start_date(self, setup_es, setup_data):
        """Tests sort by start_date desc."""
        start_date_a = datetime.date(2011, 9, 29)
        start_date_b = datetime.date(2011, 9, 30)
        EventFactory(start_date=start_date_a)
        EventFactory(start_date=start_date_b)
        setup_es.indices.refresh()

        url = reverse('api-v3:search:event')

        response = self.api_client.post(url, {
            'start_date_after': start_date_a,
            'start_date_before': start_date_b,
            'sortby': 'start_date:desc',
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        assert len(response.data['results']) == 2
        assert response.data['results'][0]['start_date'] == start_date_b.isoformat()
        assert response.data['results'][1]['start_date'] == start_date_a.isoformat()

    def test_search_event_sortby_end_date(self, setup_es, setup_data):
        """Tests sort by end_date desc."""
        start_date = datetime.date(2000, 9, 29)
        end_date_a = datetime.date(2014, 9, 29)
        end_date_b = datetime.date(2015, 9, 29)
        EventFactory(start_date=start_date, end_date=end_date_a)
        EventFactory(start_date=start_date, end_date=end_date_b)
        setup_es.indices.refresh()

        url = reverse('api-v3:search:event')

        response = self.api_client.post(url, {
            'original_query': '',
            'start_date_after': start_date,
            'start_date_before': start_date,
            'sortby': 'end_date:desc',
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        assert len(response.data['results']) == 2
        assert response.data['results'][0]['end_date'] == end_date_b.isoformat()
        assert response.data['results'][1]['end_date'] == end_date_a.isoformat()

    def test_search_event_sortby_modified_on(self, setup_es, setup_data):
        """Tests sort by modified_on desc."""
        start_date = datetime.date(2001, 9, 29)
        event_a = EventFactory(start_date=start_date)
        event_b = EventFactory(start_date=start_date)
        event_a.name = 'testing'
        event_a.save()
        setup_es.indices.refresh()

        url = reverse('api-v3:search:event')

        response = self.api_client.post(url, {
            'start_date_after': start_date,
            'start_date_before': start_date,
            'sortby': 'modified_on:desc',
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        assert len(response.data['results']) == 2
        assert response.data['results'][0]['id'] == str(event_a.id)
        assert response.data['results'][1]['id'] == str(event_b.id)


class TestBasicSearch(APITestMixin):
    """Tests basic search view."""

    def test_all_events(self, setup_es, setup_data):
        """Tests basic aggregate all events query."""
        setup_es.indices.refresh()

        term = ''

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(url, {
            'term': term,
            'entity': 'event'
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] > 0

    def test_aggregations(self, setup_es, setup_data):
        """Tests basic aggregate events query."""
        EventFactory(name='abcdefghijkl')
        EventFactory(name='abcdefghijkm')
        setup_es.indices.refresh()

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(url, {
            'term': 'abcdefg',
            'entity': 'event'
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        assert response.data['results'][0]['name'].startswith('abcdefg')
        assert [{'count': 2, 'entity': 'event'}] == response.data['aggregations']

    def test_no_results(self, setup_es, setup_data):
        """Tests case where there should be no results."""
        setup_es.indices.refresh()

        term = 'there-should-be-no-match'

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(url, {
            'term': term,
            'entity': 'event'
        })

        assert response.data['count'] == 0
