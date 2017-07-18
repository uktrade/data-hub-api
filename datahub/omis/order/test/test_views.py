import pytest
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core import constants
from datahub.core.test_utils import APITestMixin
from .factories import CompanyFactory, ContactFactory

# mark the whole module for db use
pytestmark = pytest.mark.django_db


class AddOrderTestCase(APITestMixin):
    """Add Order test case."""

    @freeze_time('2017-04-18 13:00:00.000000+00:00')
    def test_success(self):
        """
        Test a successful call to create an Order.
        """
        company = CompanyFactory()
        contact = ContactFactory(company=company)
        country = constants.Country.france.value

        url = reverse('api-v3:omis:order:list')
        response = self.api_client.post(url, {
            'company': {
                'id': company.pk
            },
            'contact': {
                'id': contact.pk
            },
            'primary_market': {
                'id': country.id
            },
        }, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json() == {
            'id': response.json()['id'],
            'reference': response.json()['reference'],
            'company': {
                'id': company.pk,
                'name': company.name
            },
            'contact': {
                'id': contact.pk,
                'name': contact.name
            },
            'primary_market': {
                'id': country.id,
                'name': country.name,
            }
        }

    def test_fails_if_contact_not_from_company(self):
        """
        Test that if the contact does not work at the company specified, the validation fails.
        """
        company = CompanyFactory()
        contact = ContactFactory()  # doesn't work at `company`
        country = constants.Country.france.value

        url = reverse('api-v3:omis:order:list')
        response = self.api_client.post(url, {
            'company': {
                'id': company.pk
            },
            'contact': {
                'id': contact.pk
            },
            'primary_market': {
                'id': country.id
            }
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'contact': ['The contact does not work at the given company.']
        }

    def test_general_validation(self):
        """
        Test create an Order general validation.
        """
        url = reverse('api-v3:omis:order:list')
        response = self.api_client.post(url, {}, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'company': ['This field is required.'],
            'contact': ['This field is required.'],
            'primary_market': ['This field is required.']
        }
