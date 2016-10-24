"""
These tests rely on the metadata.yaml fixture to be imported,
Check conftest.py in the root folder for the importing mechanism.
"""

import pytest
from django.conf import settings
from django.core.exceptions import ValidationError

from django.urls import reverse
from rest_framework import status

from core import constants
from es.services import document_exists
from es.utils import get_elasticsearch_client

from company import models
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
    assert response.data['count'] == models.Company.objects.all().count()


def test_detail_company_with_company_number(api_client):
    """Test company detail view with companies house data.

    Make sure that the registered name and registered address are coming from CH data
    """

    pk = 'a73efeba-8499-11e6-ae22-56b6b6499611'

    url = reverse('company-detail', kwargs={'pk': pk})
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data['id'] == str(pk)

    assert response.data['companies_house_data']
    assert response.data['companies_house_data']['id'] == 1
    assert response.data['name'] == 'Mercury trading'
    assert response.data['registered_address'] == {
        'address_1': '64 Ermin Street',
        'address_2': None,
        'address_3': None,
        'address_4': None,
        'address_town': 'Y Ffor',
        'address_country': '80756b9a-5d95-e211-a939-e4115bead28a',
        'address_county': None,
        'address_postcode': 'LL53 5RN',
    }


def test_detail_company_without_company_number(api_client):
    """Test company detail view without companies house data.

    Make sure that the registered name and address are coming from CDMS.
    """

    pk = '0f5216e0-849f-11e6-ae22-56b6b6499611'
    url = reverse('company-detail', kwargs={'pk': pk})
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data['id'] == str(pk)

    assert response.data['companies_house_data'] is None
    assert response.data['name'] == 'Venus ltd'
    assert response.data['registered_address'] == {
        'address_1': '66 Marcham Road',
        'address_2': None,
        'address_3': None,
        'address_4': None,
        'address_town': 'Bordley',
        'address_country': '80756b9a-5d95-e211-a939-e4115bead28a',
        'address_county': None,
        'address_postcode': 'BD23 8RZ',
    }


def test_update_company(api_client):
    """Test company update."""

    pk = '0f5216e0-849f-11e6-ae22-56b6b6499611'
    url = reverse('company-detail', kwargs={'pk': pk})
    response = api_client.patch(url, {
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
        'alias': None,
        'business_type': constants.BusinessType.company.value.id,
        'sector': constants.Sector.aerospace_assembly_aircraft.value.id,
        'registered_address_country': constants.Country.united_kingdom.value.id,
        'registered_address_1': '75 Stramford Road',
        'registered_address_town': 'London',
        'uk_region': constants.UKRegion.england.value.id
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


def test_add_company_partial_trading_address(api_client):
    """Test add new company with partial trading address."""

    url = reverse('company-list')

    with pytest.raises(ValidationError) as error:
        api_client.post(url, {
            'name': 'Acme',
            'business_type': constants.BusinessType.company.value.id,
            'sector': constants.Sector.aerospace_assembly_aircraft.value.id,
            'registered_address_country': constants.Country.united_kingdom.value.id,
            'registered_address_1': '75 Stramford Road',
            'registered_address_town': 'London',
            'trading_address_1': 'test',
            'uk_region': constants.UKRegion.england.value.id
        })

    assert 'If a trading address is specified, it must be complete.' in str(error.value)


def test_add_company_with_trading_address(api_client):
    """Test add new company with trading_address."""

    url = reverse('company-list')
    response = api_client.post(url, {
        'name': 'Acme',
        'business_type': constants.BusinessType.company.value.id,
        'sector': constants.Sector.aerospace_assembly_aircraft.value.id,
        'registered_address_country': constants.Country.united_kingdom.value.id,
        'registered_address_1': '75 Stramford Road',
        'registered_address_town': 'London',
        'trading_address_country': constants.Country.ireland.value.id,
        'trading_address_1': '1 Hello st.',
        'trading_address_town': 'Dublin',
        'uk_region': constants.UKRegion.england.value.id
    })

    assert response.status_code == status.HTTP_201_CREATED

    # make sure we're writing to ES
    es_client = get_elasticsearch_client()
    assert document_exists(
        client=es_client,
        doc_type='company_company',
        document_id=response.data['id']
    )


def test_archive_company_no_reason(api_client):
    """Test company archive."""

    pk = 'a73efeba-8499-11e6-ae22-56b6b6499611'
    url = reverse('company-archive', kwargs={'pk': pk})
    response = api_client.post(url)

    assert response.data['archived']
    assert response.data['archived_reason'] == ''
    assert response.data['id'] == pk

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

    pk = 'a73efeba-8499-11e6-ae22-56b6b6499611'
    url = reverse('company-archive', kwargs={'pk': pk})
    response = api_client.post(url, {'reason': 'foo'})

    assert response.data['archived']
    assert response.data['archived_reason'] == 'foo'
    assert response.data['id'] == pk

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

def test_list_ch_companies(api_client):
    """List the companies house companies."""

    CompaniesHouseCompanyFactory()
    CompaniesHouseCompanyFactory()

    url = reverse('companieshousecompany-list')
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] ==  models.CompaniesHouseCompany.objects.all().count()


def test_detail_ch_company(api_client):
    """Test companies house company detail."""

    ch_company = CompaniesHouseCompanyFactory(company_number=123)

    url = reverse('companieshousecompany-detail', kwargs={'company_number': ch_company.company_number})
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data['id'] == ch_company.id


def test_ch_company_cannot_be_written(api_client):
    """Test CH company POST is not allowed."""

    url = reverse('companieshousecompany-list')
    response = api_client.post(url)

    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

