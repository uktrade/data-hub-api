import pytest
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core import constants
from datahub.core.test_utils import LeelooTestCase
from .factories import CompanyFactory, ContactFactory

# mark the whole module for db use
pytestmark = pytest.mark.django_db


class AddContactTestCase(LeelooTestCase):
    """Add contact test case."""

    @freeze_time('2017-04-18 13:25:30.986208+00:00')
    def test_with_address_same_as_company(self):
        """Test add new contact with same address as company."""

        url = reverse('api-v3:contact:list')
        company = CompanyFactory()
        response = self.api_client.post(url, {
            'first_name': 'Oratio',
            'last_name': 'Nelson',
            'title': constants.Title.admiral_of_the_fleet.value.id,
            'company': company.pk,
            'job_title': constants.Role.owner.value.name,
            'email': 'foo@bar.com',
            'telephone_countrycode': '+44',
            'telephone_number': '123456789',
            'address_same_as_company': True,
            'primary': True,
            'contactable_by_email': True
        })

        assert response.status_code == status.HTTP_201_CREATED
        expected_response = {
            'address_1': None,
            'address_2': None,
            'address_3': None,
            'address_4': None,
            'address_country': None,
            'address_county': None,
            'address_postcode': None,
            'address_same_as_company': True,
            'address_town': None,
            'advisor': str(self.user.pk),
            'archived': False,
            'archived_by': None,
            'archived_on': None,
            'archived_reason': None,
            'company': str(company.pk),
            'contactable_by_dit': False,
            'contactable_by_dit_partners': False,
            'contactable_by_email': True,
            'contactable_by_phone': False,
            'created_on': '2017-04-18T13:25:30.986208',
            'email': 'foo@bar.com',
            'email_alternative': None,
            'first_name': 'Oratio',
            'id': response.json()['id'],
            'job_title': 'Owner',
            'last_name': 'Nelson',
            'modified_on': '2017-04-18T13:25:30.986208',
            'notes': None,
            'primary': True,
            'telephone_alternative': None,
            'telephone_countrycode': '+44',
            'telephone_number': '123456789',
            'title': constants.Title.admiral_of_the_fleet.value.id
        }
        assert response.json() == expected_response

    def test_fails_with_invalid_email_address(self):
        """Test that fails if the email address is invalid."""

        url = reverse('api-v3:contact:list')
        response = self.api_client.post(url, {
            'first_name': 'Oratio',
            'last_name': 'Nelson',
            'title': constants.Title.admiral_of_the_fleet.value.id,
            'company': CompanyFactory().pk,
            'job_title': constants.Role.owner.value.name,
            'email': 'invalid dot com',
            'telephone_countrycode': '+44',
            'telephone_number': '123456789',
            'address_same_as_company': True,
            'primary': True
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {
            'email': ['Enter a valid email address.']
        }

    def test_fails_without_address(self):
        """Test that fails without any address."""

        url = reverse('api-v3:contact:list')
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

    def test_fails_with_only_partial_manual_address(self):
        """Test that fails if only partial manual address supplied."""

        url = reverse('api-v3:contact:list')
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

    def test_with_manual_address(self):
        """Test add with manual address."""

        url = reverse('api-v3:contact:list')
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
            'primary': True,
            'contactable_by_email': True
        })

        assert response.status_code == status.HTTP_201_CREATED

    def test_fails_with_contact_preferences_not_set(self):
        """Test that fails without any contact preference."""

        url = reverse('api-v3:contact:list')
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
            'primary': True,
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['errors'] == {
            'contactable_by_email': [
                'A contact should have at least one way of being contacted. '
                'Please select either email or phone, or both'
            ],
            'contactable_by_phone': [
                'A contact should have at least one way of being contacted. '
                'Please select either email or phone, or both'
            ]
        }

    def test_fails_with_all_contact_preferences_set_to_false(self):
        """At least one contact preference has to be True, this tests
        that if all are set to False, it fails."""

        url = reverse('api-v3:contact:list')
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
            'primary': True,
            'contactable_by_email': False,
            'contactable_by_phone': False
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['errors'] == {
            'contactable_by_email': [
                'A contact should have at least one way of being contacted. '
                'Please select either email or phone, or both'
            ],
            'contactable_by_phone': [
                'A contact should have at least one way of being contacted. '
                'Please select either email or phone, or both'
            ]
        }


class EditContactTestCase(LeelooTestCase):
    """Edit contact test case."""

    def test_edit(self):
        """Test that it successfully edits an existing contact."""

        contact = ContactFactory(first_name='Foo')
        url = reverse('api-v3:contact:detail', kwargs={'pk': contact.pk})
        response = self.api_client.patch(url, {
            'first_name': 'bar',
        })

        assert response.status_code == status.HTTP_200_OK, response.data
        assert response.data['first_name'] == 'bar'


class ArchiveContactTestCase(LeelooTestCase):
    """Archive/unarchive contact test case."""

    def test_archive_without_reason(self):
        """Test archive contact without providing a reason."""

        contact = ContactFactory()
        url = reverse('api-v3:contact:archive', kwargs={'pk': contact.pk})
        response = self.api_client.post(url)

        assert response.data['archived']
        assert response.data['archived_reason'] == ''
        assert response.data['id'] == contact.pk

    def test_archive_with_reason(self):
        """Test archive contact providing a reason."""

        contact = ContactFactory()
        url = reverse('api-v3:contact:archive', kwargs={'pk': contact.pk})
        response = self.api_client.post(url, {'reason': 'foo'})

        assert response.data['archived']
        assert response.data['archived_reason'] == 'foo'
        assert response.data['id'] == contact.pk

    def test_unarchive(self):
        """Test unarchive contact."""

        contact = ContactFactory(archived=True, archived_reason='foo')
        url = reverse('api-v3:contact:unarchive', kwargs={'pk': contact.pk})
        response = self.api_client.get(url)

        assert not response.data['archived']
        assert response.data['archived_reason'] == ''
        assert response.data['id'] == contact.pk


class ViewContactTestCase(LeelooTestCase):
    """View contact test case."""

    def test_view(self):
        """Test view."""

        contact = ContactFactory()
        url = reverse('api-v3:contact:detail', kwargs={'pk': contact.pk})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == contact.pk
