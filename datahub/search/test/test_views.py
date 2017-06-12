import datetime

import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core import constants
from datahub.core.test_utils import LeelooTestCase

pytestmark = pytest.mark.django_db


@pytest.mark.usefixtures('setup_data')
class SearchTestCase(LeelooTestCase):
    """Tests search views."""

    def test_basic_search_companies(self):
        """Tests basic aggregate companies query."""
        term = 'abc defg'

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(url, {
            'term': term,
            'entity': 'company'
        })

        assert response.data['count'] == 3
        assert response.data['companies'][0]['name'].startswith(term)
        assert [{'count': 3, 'entity': 'company'},
                {'count': 1, 'entity': 'contact'}] == response.data['aggregations']

    def test_basic_search_contacts(self):
        """Tests basic aggregate contacts query."""
        term = 'abc defg'

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(url, {
            'term': term,
            'entity': 'contact'
        })

        assert response.data['count'] == 1
        assert response.data['contacts'][0]['first_name'] in term
        assert response.data['contacts'][0]['last_name'] in term
        assert [{'count': 3, 'entity': 'company'},
                {'count': 1, 'entity': 'contact'}] == response.data['aggregations']

    def test_basic_search_companies_no_results(self):
        """Tests case where there should be no results."""
        term = 'there-should-be-no-match'

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(url, {
            'term': term,
            'entity': 'company'
        })

        assert response.data['count'] == 0

    def test_basic_search_companies_no_term(self):
        """Tests case where there is not term provided."""
        url = reverse('api-v3:search:basic')
        response = self.api_client.get(url, {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_basic_search_companies_invalid_entity(self):
        """Tests case where provided entity is invalid."""
        url = reverse('api-v3:search:basic')
        response = self.api_client.get(url, {
            'term': 'test',
            'entity': 'sloths',
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_basic_search_paging(self):
        """Tests pagination of results."""
        term = 'abc defg'

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(url, {
            'term': term,
            'entity': 'company',
            'offset': 1,
            'limit': 1,
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 3
        assert len(response.data['companies']) == 1

    def test_search_company(self):
        """Tests detailed company search."""
        term = 'abc defg'

        url = f"{reverse('api-v3:search:company')}?offset=0&limit=100"

        response = self.api_client.post(url, {
            'original_query': term,
            'trading_address_country': constants.Country.united_states.value.id,
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['trading_address_country']['id'] == constants.Country.united_states.value.id

    def test_search_company_no_filters(self):
        """Tests case where there is no filters provided."""
        url = f"{reverse('api-v3:search:company')}?offset=0&limit=100"
        response = self.api_client.post(url, {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_search_foreign_company_json(self):
        """Tests detailed company search."""
        url = f"{reverse('api-v3:search:company')}?offset=0&limit=100"

        response = self.api_client.post(url, {
            'uk_based': False,
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['uk_based'] is False

    def test_search_contact(self):
        """Tests detailed contact search."""
        term = 'abc defg'

        url = f"{reverse('api-v3:search:contact')}?offset=0&limit=100"

        response = self.api_client.post(url, {
            'original_query': term,
            'last_name': 'defg',
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['last_name'] == 'defg'

    def test_search_contact_no_filters(self):
        """Tests case where there is no filters provided."""
        url = f"{reverse('api-v3:search:contact')}?offset=0&limit=100"
        response = self.api_client.post(url, {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_search_investment_project_json(self):
        """Tests detailed investment project search."""
        url = f"{reverse('api-v3:search:investment_project')}?offset=0&limit=100"

        response = self.api_client.post(url, {
            'description': 'investmentproject1',
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['description'] == 'investmentproject1'

    def test_search_investment_project_date_json(self):
        """Tests detailed investment project search."""
        url = f"{reverse('api-v3:search:investment_project')}?offset=0&limit=100"

        response = self.api_client.post(url, {
            'estimated_land_date_before': datetime.datetime(2017, 6, 13, 9, 44, 31, 62870),
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert len(response.data['results']) == 1

    def test_search_investment_project_no_filters(self):
        """Tests case where there is no filters provided."""
        url = f"{reverse('api-v3:search:investment_project')}?offset=0&limit=100"
        response = self.api_client.post(url, {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
