import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.test_utils import APITestMixin
from datahub.event.test.factories import EventFactory


@pytest.fixture
def setup_data():
    """Sets up data for the tests."""
    EventFactory()
    EventFactory()


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
            'original_query': '',
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

    def test_events(self, setup_es, setup_data):
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
