import datetime
from unittest import mock, skip

import pytest
from elasticsearch_dsl.connections import connections
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import CompanyFactory
from datahub.core import constants
from datahub.core.test_utils import (
    LeelooTestCase, synchronous_executor_submit, synchronous_transaction_on_commit,
)

pytestmark = pytest.mark.django_db


@pytest.mark.usefixtures('setup_data', 'post_save_handlers')
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

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 3
        assert response.data['companies'][0]['name'].startswith(term)
        assert [{'count': 3, 'entity': 'company'},
                {'count': 1, 'entity': 'contact'},
                {'count': 1, 'entity': 'investment_project'}] == response.data['aggregations']

    def test_basic_search_contacts(self):
        """Tests basic aggregate contacts query."""
        term = 'abc defg'

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(url, {
            'term': term,
            'entity': 'contact'
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['contacts'][0]['first_name'] in term
        assert response.data['contacts'][0]['last_name'] in term
        assert [{'count': 3, 'entity': 'company'},
                {'count': 1, 'entity': 'contact'},
                {'count': 1, 'entity': 'investment_project'}] == response.data['aggregations']

    def test_basic_search_investment_projects(self):
        """Tests basic aggregate investment project query."""
        term = 'abc defg'

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(url, {
            'term': term,
            'entity': 'investment_project'
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['investment_projects'][0]['name'] == term
        assert [{'count': 3, 'entity': 'company'},
                {'count': 1, 'entity': 'contact'},
                {'count': 1, 'entity': 'investment_project'}] == response.data['aggregations']

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

    def test_search_investment_project_invalid_date_json(self):
        """Tests detailed investment project search."""
        url = f"{reverse('api-v3:search:investment_project')}?offset=0&limit=100"

        response = self.api_client.post(url, {
            'estimated_land_date_before': 'this is definitely not a valid date',
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_search_investment_project_no_filters(self):
        """Tests case where there is no filters provided."""
        url = f"{reverse('api-v3:search:investment_project')}?offset=0&limit=100"
        response = self.api_client.post(url, {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @skip('This test fails randomly. Skip until fixed.')
    @mock.patch('datahub.core.utils.executor.submit', synchronous_executor_submit)
    @mock.patch('django.db.transaction.on_commit', synchronous_transaction_on_commit)
    def test_search_results_quality(self):
        """Tests quality of results."""
        CompanyFactory(name='The Risk Advisory Group').save()
        CompanyFactory(name='The Advisory Group').save()
        CompanyFactory(name='The Advisory').save()
        CompanyFactory(name='The Advisories').save()

        connections.get_connection().indices.refresh()

        term = 'The Advisory'

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(url, {
            'term': term,
            'entity': 'company'
        })

        assert response.data['count'] == 4
        assert ['The Advisory',
                'The Advisory Group',
                'The Risk Advisory Group',
                'The Advisories'] == [company['name'] for company in response.data['companies']]
