"""
These tests rely on the metadata.yaml fixture to be imported,
Check conftest.py in the root folder for the importing mechanism.
"""
import uuid

import pytest
from django.conf import settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from company.models import Company, Contact
from users.models import Advisor
from company.test import factories
from core import constants
from korben.utils import generate_signature

# mark the whole module for db use
pytestmark = pytest.mark.django_db


def _signature(url, data):
    """Return the signature to authenticate the api client for the tests in this module."""
    return generate_signature(
        url,
        APIClient()._encode_data(data)[0],
        settings.DATAHUB_SECRET
    )


def test_korben_company_create(api_client):
    """Create a company."""

    url = reverse('korben:company_company')
    data = {
        'id': str(uuid.uuid4()),
        'name': 'Foo',
        'registered_address_1': 'Foo st.',
        'registered_address_town': 'London',
        'registered_address_country_id': constants.Country.united_kingdom.value.id,
        'business_type_id': constants.BusinessType.private_limited_company.value.id,
        'sector_id': constants.Sector.aerospace_assembly_aircraft.value.id,
        'archived': False,
        'uk_region_id': constants.UKRegion.england.value.id,
    }

    api_client.credentials(**{'X-Signature': _signature(url, data)})
    response = api_client.post(url, data)

    assert response.status_code == status.HTTP_200_OK
    assert Company.objects.get(pk=data['id'])


def test_korben_company_update(api_client):
    """Update a company."""

    url = reverse('korben:company_company')
    company = factories.CompanyFactory()

    data = {
        'id': str(company.id),
        'name': 'My little company',
        'registered_address_1': 'My st.',
        'registered_address_town': 'London',
        'registered_address_country_id': constants.Country.united_kingdom.value.id,
        'business_type_id': constants.BusinessType.private_limited_company.value.id,
        'sector_id': constants.Sector.aerospace_assembly_aircraft.value.id,
        'archived': False,
        'uk_region_id': constants.UKRegion.england.value.id,
    }
    api_client.credentials(**{'X-Signature': _signature(url, data)})
    response = api_client.post(url, data)

    assert response.status_code == status.HTTP_200_OK
    assert Company.objects.filter(pk=data['id'], name='My little company').exists()


def test_korben_contact_create(api_client):
    """Create a contact."""

    company = factories.CompanyFactory()
    url = reverse('korben:company_contact')
    data = {
        'id': str(uuid.uuid4()),
        'title_id': constants.Title.wing_commander.value.id,
        'first_name': 'John',
        'last_name': 'Smith',
        'role_id': constants.Role.owner.value.id,
        'company_id': company.id,
        'email': 'foo@bar.com',
        'telephone_countrycode': '+44',
        'telephone_number': '123456789',
        'address_same_as_company': True,
        'primary': True
    }
    api_client.credentials(**{'X-Signature': _signature(url, data)})
    response = api_client.post(url, data)

    assert response.status_code == status.HTTP_200_OK
    assert Contact.objects.get(pk=data['id'])


def test_korben_contact_incomplete_address_create(api_client):
    """Create a contact with incomplete address."""

    company = factories.CompanyFactory()
    url = reverse('korben:company_contact')
    data = {
        'id': str(uuid.uuid4()),
        'title_id': constants.Title.wing_commander.value.id,
        'first_name': 'Bat',
        'last_name': 'Man',
        'role_id': constants.Role.owner.value.id,
        'company_id': company.id,
        'email': 'foo@bar.com',
        'telephone_countrycode': '+44',
        'telephone_number': '123456789',
        'address_1': '14 Hello street',
        'primary': True
    }
    api_client.credentials(**{'X-Signature': _signature(url, data)})
    response = api_client.post(url, data)

    assert response.status_code == status.HTTP_200_OK
    assert Contact.objects.get(pk=data['id'])


def test_korben_contact_update(api_client):
    """Update a contact."""

    contact = factories.ContactFactory()
    url = reverse('korben:company_contact')
    data = {
        'id': str(uuid.uuid4()),
        'title_id': constants.Title.wing_commander.value.id,
        'first_name': 'Mario',
        'last_name': 'Smith',
        'role_id': constants.Role.owner.value.id,
        'company_id': contact.company.id,
        'email': 'foo@bar.com',
        'telephone_countrycode': '+44',
        'telephone_number': '123456789',
        'address_same_as_company': True,
        'primary': True
    }
    api_client.credentials(**{'X-Signature': _signature(url, data)})
    response = api_client.post(url, data)

    assert response.status_code == status.HTTP_200_OK
    assert Contact.objects.filter(pk=data['id'], first_name='Mario').exists()


def test_korben_advisor_create(api_client):
    """Create an advisor."""

    url = reverse('korben:company_advisor')
    data = {
        'id': str(uuid.uuid4()),
        'first_name': 'John',
        'last_name': 'Smith',
        'dit_team_id': constants.Team.healthcare_uk.value.id,
    }
    api_client.credentials(**{'X-Signature': _signature(url, data)})
    response = api_client.post(url, data)

    assert response.status_code == status.HTTP_200_OK
    assert Advisor.objects.get(pk=data['id'])
