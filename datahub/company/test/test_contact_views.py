import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core import constants
from datahub.core.test_utils import LeelooTestCase
from .factories import CompanyFactory, ContactFactory

# mark the whole module for db use
pytestmark = pytest.mark.django_db


class ContactTestCase(LeelooTestCase):
    """Contact test case."""

    def test_add_contact_address_same_as_company(self):
        """Test add new contact."""
        url = reverse('v1:contact-list')
        response = self.api_client.post(url, {
            'first_name': 'Oratio',
            'last_name': 'Nelson',
            'title': constants.Title.admiral_of_the_fleet.value.id,
            'company': CompanyFactory().pk,
            'job_title': constants.Role.owner.value.name,
            'email': 'foo@bar.com',
            'telephone_countrycode': '+44',
            'telephone_number': '123456789',
            'address_same_as_company': True,
            'primary': True
        })

        assert response.status_code == status.HTTP_201_CREATED

    def test_add_contact_no_address(self):
        """Test add new contact without any address."""
        url = reverse('v1:contact-list')
        response = self.api_client.post(url, {
            'first_name': 'Oratio',
            'last_name': 'Nelson',
            'title': constants.Title.admiral_of_the_fleet.value.id,
            'company': CompanyFactory().pk,
            'job_title': constants.Role.owner.value.name,
            'email': 'foo@bar.com',
            'telephone_countrycode': '+44',
            'telephone_number': '123456789',
            'primary': True
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['errors'] == {
            'address_same_as_company': ['Please select either address_same_as_company or enter an address manually.']
        }

    def test_add_contact_partial_manual_address(self):
        """Test add new contact with a partial manual address."""
        url = reverse('v1:contact-list')

        response = self.api_client.post(url, {
            'first_name': 'Oratio',
            'last_name': 'Nelson',
            'title': constants.Title.admiral_of_the_fleet.value.id,
            'company': CompanyFactory().pk,
            'job_title': constants.Role.owner.value.name,
            'email': 'foo@bar.com',
            'telephone_countrycode': '+44',
            'telephone_number': '123456789',
            'address_1': 'test',
            'primary': True
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['errors'] == {
            'address_country': ['This field may not be null.'],
            'address_town': ['This field may not be null.']
        }

    def test_add_contact_manual_address(self):
        """Test add new contact manual address."""
        url = reverse('v1:contact-list')
        response = self.api_client.post(url, {
            'first_name': 'Oratio',
            'last_name': 'Nelson',
            'title': constants.Title.admiral_of_the_fleet.value.id,
            'company': CompanyFactory().pk,
            'job_title': constants.Role.owner.value.name,
            'email': 'foo@bar.com',
            'telephone_countrycode': '+44',
            'telephone_number': '123456789',
            'address_1': 'Foo st.',
            'address_town': 'London',
            'address_country': constants.Country.united_kingdom.value.id,
            'primary': True
        })

        assert response.status_code == status.HTTP_201_CREATED

    def test_modify_contact(self):
        """Modify an existing contact."""
        contact = ContactFactory(first_name='Foo')
        url = reverse('v1:contact-detail', kwargs={'pk': contact.pk})
        response = self.api_client.patch(url, {
            'first_name': 'bar',
        })

        assert response.status_code == status.HTTP_200_OK, response.data
        assert response.data['first_name'] == 'bar'

    def test_archive_contact_no_reason(self):
        """Test archive contact without providing a reason."""
        contact = ContactFactory()
        url = reverse('v1:contact-archive', kwargs={'pk': contact.pk})
        response = self.api_client.post(url)

        assert response.data['archived']
        assert response.data['archived_reason'] == ''
        assert response.data['id'] == contact.pk

    def test_archive_contact_reason(self):
        """Test archive contact providing a reason."""
        contact = ContactFactory()
        url = reverse('v1:contact-archive', kwargs={'pk': contact.pk})
        response = self.api_client.post(url, {'reason': 'foo'})

        assert response.data['archived']
        assert response.data['archived_reason'] == 'foo'
        assert response.data['id'] == contact.pk

    def test_unarchive_contact(self):
        """Test unarchive contact."""
        contact = ContactFactory(archived=True, archived_reason='foo')
        url = reverse('v1:contact-unarchive', kwargs={'pk': contact.pk})
        response = self.api_client.get(url)

        assert not response.data['archived']
        assert response.data['archived_reason'] == ''
        assert response.data['id'] == contact.pk

    def test_contact_detail_view(self):
        """Contact detail view."""
        contact = ContactFactory()
        url = reverse('v1:contact-detail', kwargs={'pk': contact.pk})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == contact.pk
