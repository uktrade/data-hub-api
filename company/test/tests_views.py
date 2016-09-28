"""These tests rely on the test_data.yaml fixture to be imported"""

import pytest
from django.conf import settings

from django.urls import reverse
from rest_framework import status

# mark the whole module for db use
from es.services import document_exists
from es.utils import get_elasticsearch_client

pytestmark = pytest.mark.django_db


COMPANY_NUMBER_COMPANY_ID = 'a73efeba-8499-11e6-ae22-56b6b6499611'
COMPANY_ID = '0f5216e0-849f-11e6-ae22-56b6b6499611'
CH_COMPANY_ID = 1
BUSINESS_TYPE_ID = '98d14e94-5d95-e211-a939-e4115bead28a' # LTD company
SECTOR_ID = '355f977b-8ac3-e211-a646-e4115bead28a'  # retail
COUNTRY_ID = '80756b9a-5d95-e211-a939-e4115bead28a'  # United Kingdom


# CDMS company views tests

def test_list_companies(api_client):
    """List the companies."""

    url = reverse('company-list')
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK


def test_detail_company_with_company_number(api_client):
    """Test company detail view with companies house data."""

    url = reverse('company-detail', kwargs={'pk': COMPANY_NUMBER_COMPANY_ID})
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data['companies_house_data']['id'] == 1


def test_detail_company_without_company_number(api_client):
    """Test company detail view without companies house data."""

    url = reverse('company-detail', kwargs={'pk': COMPANY_ID})
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data['companies_house_data'] == {}


def test_update_company(api_client):
    """Test company update."""

    # add the company first
    url = reverse('company-list')
    response = api_client.post(url, {
        'name': 'Foo',
        'business_type': BUSINESS_TYPE_ID,
        'sector': SECTOR_ID,
        'country': COUNTRY_ID,
        'address_1': '75 Stramford Road',
        'address_postcode': 'SP10 4ET'
    })
    assert response.status_code == status.HTTP_201_CREATED

    # now update it
    url = reverse('company-detail', kwargs={'pk': response.data['id']})
    response = api_client.put(url, {
        'name': 'Acme',
    })

    assert response.status_code == status.HTTP_200_OK
    assert response.data['name'] == 'Acme'

    # make sure we're writing to ES
    es_client = get_elasticsearch_client()
    es_result = es_client.get(
        index=settings.ES_INDEX,
        doc_type='company_company',
        id=response.data['id'],
        realtime=True
    )
    assert es_result['_source']['name'] == 'Acme'


def test_add_company(api_client):
    """Test add new company."""

    url = reverse('company-list')
    response = api_client.post(url, {
        'name': 'Acme',
        'business_type': BUSINESS_TYPE_ID,
        'sector': SECTOR_ID,
        'country': COUNTRY_ID,
        'address_1': '75 Stramford Road',
        'address_postcode': 'SP10 4ET'
    })

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['name'] == 'Acme'

    # make sure we're writing to ES
    es_client = get_elasticsearch_client()
    assert document_exists(
        client=es_client,
        doc_type='company_company',
        document_id=response.data['id']
    )

