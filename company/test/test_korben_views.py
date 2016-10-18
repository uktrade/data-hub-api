"""
These tests rely on the metadata.yaml fixture to be imported,
Check conftest.py in the root folder for the importing mechanism.
"""
import uuid

import pytest

from django.urls import reverse

# mark the whole module for db use
from rest_framework import status

from company.models import Company
from core import constants

from . import factories

pytestmark = pytest.mark.django_db


def test_korben_company_create(api_client):
    """Create a company"""

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
    response = api_client.post(url, data)

    assert response.status_code == status.HTTP_200_OK
    assert Company.objects.get(pk=data['id'])


def test_korben_company_update(api_client):
    """Update a company"""

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
    response = api_client.post(url, data)

    assert response.status_code == status.HTTP_200_OK
    company_from_db = Company.objects.get(pk=data['id'])
    assert company_from_db.name == 'My little company'

