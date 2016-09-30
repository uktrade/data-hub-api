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

from .factories import CompanyFactory, ContactFactory

# mark the whole module for db use
pytestmark = pytest.mark.django_db


def test_add_contact(api_client):
    """Test add new contact."""

    url = reverse('contact-list')
    response = api_client.post(url, {
        'name': 'Oratio Nelson',
        'title': constants.Title.admiral_of_the_fleet.value.id,
        'company': CompanyFactory().pk
    })

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['name'] == 'Oratio Nelson'

    # make sure we're writing to ES
    es_client = get_elasticsearch_client()
    assert document_exists(
        client=es_client,
        doc_type='company_contact',
        document_id=response.data['id']
    )


def test_modify_contact(api_client):
    """Modify an existing contact."""

    contact = ContactFactory(name='foo')

    url = reverse('contact-detail', kwargs={'pk': contact.pk})
    response = api_client.put(url, {
        'name': 'bar',
    })

    assert response.status_code == status.HTTP_200_OK
    assert response.data['name'] == 'bar'

    # make sure we're writing to ES
    es_client = get_elasticsearch_client()
    es_result = es_client.get(
        index=settings.ES_INDEX,
        doc_type='company_contact',
        id=response.data['id'],
        realtime=True
    )
    assert es_result['_source']['name'] == 'bar'


def test_archive_contact_no_reason(api_client):
    """Test archive contact without providing a reason."""

    contact = ContactFactory()
    url = reverse('contact-archive', kwargs={'pk': contact.id})
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
    url = reverse('contact-archive', kwargs={'pk': contact.id})
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
    url = reverse('contact-detail', kwargs={'pk': contact.id})
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data['id'] == str(contact.pk)
