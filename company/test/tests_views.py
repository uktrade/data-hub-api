"""
These tests rely on the metadata.yaml fixture to be imported,
Check conftest.py in the root folder for the importing mechanism.
"""

import pytest
from django.conf import settings

from django.urls import reverse
from rest_framework import status

from core import constants
from es.services import document_exists
from es.utils import get_elasticsearch_client

from .factories import CompanyFactory, CompaniesHouseCompanyFactory

# mark the whole module for db use
pytestmark = pytest.mark.django_db


# CDMS company views tests

def test_list_companies(api_client):
    """List the companies."""

    CompanyFactory()
    CompanyFactory()
    url = reverse('company-list')
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] == 2


def test_detail_company_with_company_number(api_client):
    """Test company detail view with companies house data."""

    ch_company = CompaniesHouseCompanyFactory(company_number=123)
    company = CompanyFactory(company_number=123)

    url = reverse('company-detail', kwargs={'pk': company.id})
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data['companies_house_data']['id'] == ch_company.id


def test_detail_company_without_company_number(api_client):
    """Test company detail view without companies house data."""

    company = CompanyFactory()

    url = reverse('company-detail', kwargs={'pk': company.id})
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data['companies_house_data'] == {}


def test_update_company(api_client):
    """Test company update."""

    # add the company first
    url = reverse('company-list')
    response = api_client.post(url, {
        'name': 'Foo',
        'business_type': constants.BusinessType.company.value.id,
        'country': constants.Country.united_kingdom.value.id,
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
        'business_type': constants.BusinessType.company.value.id,
        'country': constants.Country.united_kingdom.value.id,
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


def test_archive_company_no_reason(api_client):
    """Test company archive."""

    company = CompanyFactory()
    url = reverse('company-archive', kwargs={'pk': company.id})
    response = api_client.post(url)

    assert response.data['archived']
    assert response.data['archived_reason'] == ''
    assert response.data['id'] == str(company.id)

    # make sure we're writing to ES
    es_client = get_elasticsearch_client()
    es_result = es_client.get(
        index=settings.ES_INDEX,
        doc_type='company_company',
        id=response.data['id'],
        realtime=True
    )
    assert es_result['_source']['archived']
    assert es_result['_source']['archived_reason'] == ''


def test_archive_company_reason(api_client):
    """Test company archive."""

    company = CompanyFactory()
    url = reverse('company-archive', kwargs={'pk': company.id})
    response = api_client.post(url, {'reason': 'foo'})

    assert response.data['archived']
    assert response.data['archived_reason'] == 'foo'
    assert response.data['id'] == str(company.id)

    # make sure we're writing to ES
    es_client = get_elasticsearch_client()
    es_result = es_client.get(
        index=settings.ES_INDEX,
        doc_type='company_company',
        id=response.data['id'],
        realtime=True
    )
    assert es_result['_source']['archived']
    assert es_result['_source']['archived_reason'] == 'foo'


# Companies house company views tests

