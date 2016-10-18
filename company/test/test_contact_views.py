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

from .factories import CompanyFactory, ContactFactory

# mark the whole module for db use
pytestmark = pytest.mark.django_db


def test_add_contact_address_same_as_company(api_client):
    """Test add new contact."""

    url = reverse('contact-list')
    response = api_client.post(url, {
        'first_name': 'Oratio',
        'last_name': 'Nelson',
        'title': constants.Title.admiral_of_the_fleet.value.id,
        'company': CompanyFactory().pk,
        'role': constants.Role.owner.value.id,
        'email': 'foo@bar.com',
        'uk_region': constants.UKRegion.england.value.id,
        'telephone_countrycode': '+44',
        'telephone_number': '123456789',
        'address_same_as_company': True,
        'primary': True
    })

    assert response.status_code == status.HTTP_201_CREATED

    # make sure we're writing to ES
    es_client = get_elasticsearch_client()
    assert document_exists(
        client=es_client,
        doc_type='company_contact',
        document_id=response.data['id']
    )


def test_add_contact_no_address(api_client):
    """Test add new contact without any address."""

    url = reverse('contact-list')

    with pytest.raises(ValidationError) as error:
        api_client.post(url, {
            'first_name': 'Oratio',
            'last_name': 'Nelson',
            'title': constants.Title.admiral_of_the_fleet.value.id,
            'company': CompanyFactory().pk,
            'role': constants.Role.owner.value.id,
            'email': 'foo@bar.com',
            'uk_region': constants.UKRegion.england.value.id,
            'telephone_countrycode': '+44',
            'telephone_number': '123456789',
            'primary': True
        })

    assert 'Please select either address_as_company or enter an address manually.' in str(error.value)


def test_add_contact_partial_manual_address(api_client):
    """Test add new contact with a partial manual address."""

    url = reverse('contact-list')

    with pytest.raises(ValidationError) as error:
        api_client.post(url, {
            'first_name': 'Oratio',
            'last_name': 'Nelson',
            'title': constants.Title.admiral_of_the_fleet.value.id,
            'company': CompanyFactory().pk,
            'role': constants.Role.owner.value.id,
            'email': 'foo@bar.com',
            'uk_region': constants.UKRegion.england.value.id,
            'telephone_countrycode': '+44',
            'telephone_number': '123456789',
            'address_1': 'test',
            'primary': True
        })

    assert 'address_1, town and country are required if an address is entered.' in str(error.value)


def test_add_contact_manual_address(api_client):
    """Test add new contact manual address."""

    url = reverse('contact-list')
    response = api_client.post(url, {
        'first_name': 'Oratio',
        'last_name': 'Nelson',
        'title': constants.Title.admiral_of_the_fleet.value.id,
        'company': CompanyFactory().pk,
        'role': constants.Role.owner.value.id,
        'email': 'foo@bar.com',
        'uk_region': constants.UKRegion.england.value.id,
        'telephone_countrycode': '+44',
        'telephone_number': '123456789',
        'address_1': 'Foo st.',
        'address_town': 'London',
        'address_country': constants.Country.united_kingdom.value.id,
        'primary': True
    })

    assert response.status_code == status.HTTP_201_CREATED

    # make sure we're writing to ES
    es_client = get_elasticsearch_client()
    assert document_exists(
        client=es_client,
        doc_type='company_contact',
        document_id=response.data['id']
    )


def test_modify_contact(api_client):
    """Modify an existing contact."""

    contact = ContactFactory(first_name='foo')

    url = reverse('contact-detail', kwargs={'pk': contact.pk})
    response = api_client.patch(url, {
        'first_name': 'bar',
    })

    assert response.status_code == status.HTTP_200_OK
    assert response.data['first_name'] == 'bar'

    # make sure we're writing to ES
    es_client = get_elasticsearch_client()
    es_result = es_client.get(
        index=settings.ES_INDEX,
        doc_type='company_contact',
        id=response.data['id'],
        realtime=True
    )
    assert es_result['_source']['first_name'] == 'bar'


def test_archive_contact_no_reason(api_client):
    """Test archive contact without providing a reason."""

    contact = ContactFactory()
    url = reverse('contact-archive', kwargs={'pk': contact.pk})
    response = api_client.post(url)

    assert response.data['archived']
    assert response.data['archived_reason'] == ''
    assert response.data['id'] == str(contact.id)

    # make sure we're writing to ES
    es_client = get_elasticsearch_client()
    es_result = es_client.get(
        index=settings.ES_INDEX,
        doc_type='company_contact',
        id=response.data['id'],
        realtime=True
    )
    assert es_result['_source']['archived']
    assert es_result['_source']['archived_reason'] == ''


def test_archive_contact_reason(api_client):
    """Test archive contact providing a reason."""

    contact = ContactFactory()
    url = reverse('contact-archive', kwargs={'pk': contact.pk})
    response = api_client.post(url, {'reason': 'foo'})

    assert response.data['archived']
    assert response.data['archived_reason'] == 'foo'
    assert response.data['id'] == str(contact.id)

    # make sure we're writing to ES
    es_client = get_elasticsearch_client()
    es_result = es_client.get(
        index=settings.ES_INDEX,
        doc_type='company_contact',
        id=response.data['id'],
        realtime=True
    )
    assert es_result['_source']['archived']
    assert es_result['_source']['archived_reason'] == 'foo'


def test_contact_detail_view(api_client):
    """Contact detail view."""

    contact = ContactFactory()
    url = reverse('contact-detail', kwargs={'pk': contact.pk})
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data['id'] == str(contact.pk)
