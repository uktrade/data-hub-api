from unittest import mock

import pytest
from rest_framework.reverse import reverse

from datahub.core import constants

pytestmark = pytest.mark.django_db


@mock.patch('datahub.search.views.elasticsearch.ES_INDEX', 'test')
def test_basic_search_companies(logged_in_api_client, setup_data):
    """Tests basic aggregate companies query."""
    term = 'abc defg'

    url = reverse('api-v3:search:basic')
    response = logged_in_api_client.get(url, {
        'term': term,
        'entity': 'company'
    })

    assert response.data['count'] == 3
    assert response.data['companies'][0]['name'].startswith(term)
    assert [{'count': 3, 'entity': 'company'},
            {'count': 1, 'entity': 'contact'}] == response.data['aggregations']


@mock.patch('datahub.search.views.elasticsearch.ES_INDEX', 'test')
def test_basic_search_contacts(logged_in_api_client, setup_data):
    """Tests basic aggregate contacts query."""
    term = 'abc defg'

    url = reverse('api-v3:search:basic')
    response = logged_in_api_client.get(url, {
        'term': term,
        'entity': 'contact'
    })

    assert response.data['count'] == 1
    assert response.data['contacts'][0]['first_name'] in term
    assert response.data['contacts'][0]['last_name'] in term
    assert [{'count': 3, 'entity': 'company'},
            {'count': 1, 'entity': 'contact'}] == response.data['aggregations']


@mock.patch('datahub.search.views.elasticsearch.ES_INDEX', 'test')
def test_basic_search_companies_no_results(logged_in_api_client, setup_data):
    """Tests case where there should be no results."""
    term = 'there-should-be-no-match'

    url = reverse('api-v3:search:basic')
    response = logged_in_api_client.get(url, {
        'term': term,
        'entity': 'company'
    })

    assert response.data['count'] == 0


@mock.patch('datahub.search.views.elasticsearch.ES_INDEX', 'test')
def test_basic_search_paging(logged_in_api_client, setup_data):
    """Tests pagination of results."""
    term = 'abc defg'

    url = reverse('api-v3:search:basic')
    response = logged_in_api_client.get(url, {
        'term': term,
        'entity': 'company',
        'offset': 1,
        'limit': 1,
    })

    assert response.data['count'] == 3
    assert len(response.data['companies']) == 1


@mock.patch('datahub.search.views.elasticsearch.ES_INDEX', 'test')
def test_search_company(logged_in_api_client, setup_data):
    """Tests detailed company search."""
    term = 'abc defg'

    url = '{}?offset={}&limit={}'.format(
        reverse('api-v3:search:company'),
        0,
        100
    )

    response = logged_in_api_client.post(url, {
        'original_query': term,
        'trading_address_country': constants.Country.united_states.value.id,
    })

    assert response.data['count'] == 1
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['trading_address_country']['id'] == constants.Country.united_states.value.id


@mock.patch('datahub.search.views.elasticsearch.ES_INDEX', 'test')
def test_search_contact(logged_in_api_client, setup_data):
    """Tests detailed contact search."""
    term = 'abc defg'

    url = '{}?offset={}&limit={}'.format(
        reverse('api-v3:search:contact'),
        0,
        100
    )

    response = logged_in_api_client.post(url, {
        'original_query': term,
        'last_name': 'defg',
    })

    assert response.data['count'] == 1
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['last_name'] == 'defg'
