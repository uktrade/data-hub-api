import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import CompanyFactory

from datahub.core import constants
from datahub.core.test_utils import APITestMixin


pytestmark = pytest.mark.django_db


@pytest.fixture
def setup_data():
    """Sets up data for the tests."""
    country_uk = constants.Country.united_kingdom.value.id
    country_us = constants.Country.united_states.value.id
    CompanyFactory(
        name='abc defg ltd',
        trading_address_1='1 Fake Lane',
        trading_address_town='Downtown',
        trading_address_country_id=country_uk
    )
    CompanyFactory(
        name='abc defg us ltd',
        trading_address_1='1 Fake Lane',
        trading_address_town='Downtown',
        trading_address_country_id=country_us,
        registered_address_country_id=country_us
    )


class TestSearch(APITestMixin):
    """Tests search views."""

    def test_search_company(self, setup_es, setup_data):
        """Tests detailed company search."""
        setup_es.indices.refresh()

        term = 'abc defg'

        url = reverse('api-v3:search:company')
        united_states_id = constants.Country.united_states.value.id

        response = self.api_client.post(url, {
            'original_query': term,
            'trading_address_country': united_states_id,
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['trading_address_country']['id'] == united_states_id

    def test_company_search_paging(self, setup_es, setup_data):
        """Tests pagination of results."""
        setup_es.indices.refresh()

        url = reverse('api-v3:search:company')
        response = self.api_client.post(url, {
            'original_query': '',
            'offset': 1,
            'limit': 1,
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] > 1
        assert len(response.data['results']) == 1

    def test_company_search_paging_query_params(self, setup_es, setup_data):
        """Tests pagination of results."""
        setup_es.indices.refresh()

        url = f"{reverse('api-v3:search:company')}?offset=1&limit=1"
        response = self.api_client.post(url, {
            'original_query': '',
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] > 1
        assert len(response.data['results']) == 1

    def test_search_company_no_filters(self, setup_es, setup_data):
        """Tests case where there is no filters provided."""
        setup_es.indices.refresh()

        url = reverse('api-v3:search:company')
        response = self.api_client.post(url, {})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) > 0

    def test_search_foreign_company_json(self, setup_es, setup_data):
        """Tests detailed company search."""
        setup_es.indices.refresh()

        url = reverse('api-v3:search:company')

        response = self.api_client.post(url, {
            'uk_based': False,
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['uk_based'] is False


class TestBasicSearch(APITestMixin):
    """Tests basic search view."""

    def test_all_companies(self, setup_es, setup_data):
        """Tests basic aggregate all companies query."""
        setup_es.indices.refresh()

        term = ''

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(url, {
            'term': term,
            'entity': 'company'
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] > 0

    def test_companies(self, setup_es, setup_data):
        """Tests basic aggregate companies query."""
        setup_es.indices.refresh()

        term = 'abc defg'

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(url, {
            'term': term,
            'entity': 'company'
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        assert response.data['companies'][0]['name'].startswith(term)
        assert [{'count': 2, 'entity': 'company'}] == response.data['aggregations']

    def test_no_results(self, setup_es, setup_data):
        """Tests case where there should be no results."""
        setup_es.indices.refresh()

        term = 'there-should-be-no-match'

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(url, {
            'term': term,
            'entity': 'company'
        })

        assert response.data['count'] == 0

    def test_companies_no_term(self, setup_es, setup_data):
        """Tests case where there is not term provided."""
        setup_es.indices.refresh()

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(url, {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
