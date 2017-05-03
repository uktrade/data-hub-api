import pytest
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core import constants
from datahub.core.test_utils import LeelooTestCase
from .factories import CompanyFactory, ContactFactory

# mark the whole module for db use
pytestmark = pytest.mark.django_db


class ContactTestCase(LeelooTestCase):
    """Contact test case."""

    @freeze_time('2017-04-18 13:25:30.986208+00:00')
    def test_add_contact_address_same_as_company(self):
        """Test add new contact."""
        url = reverse('v1:contact-list')
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
        expected_response = {'address_1': None,
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
                             'title': constants.Title.admiral_of_the_fleet.value.id}
        assert response.json() == expected_response

    def test_add_contact_invalid_email_address(self):
        """Test add new contact."""
        url = reverse('v1:contact-list')
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
        assert response.content == b'{"email":["Enter a valid email address."]}'

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
            'primary': True,
            'contactable_by_email': True
        })

        assert response.status_code == status.HTTP_201_CREATED

    def test_add_contact_with_contact_preferences_not_set(self):
        """Don't set any contact preference."""
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
            'primary': True,
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        expected_response = {'errors': {'contactable_by_email': ['A contact should have at least one way of being '
                                                                 'contacted. Please select either email or phone, '
                                                                 'or both'],
                                        'contactable_by_phone': ['A contact should have at least one way '
                                                                 'of being contacted. Please select either '
                                                                 'email or phone, or both']}}
        assert response.json() == expected_response

    def test_add_contact_with_contact_preferences_set_to_false(self):
        """Contact preference both set to false."""
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
            'primary': True,
            'contactable_by_email': False,
            'contactable_by_phone': False
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        expected_response = {'errors': {'contactable_by_email': ['A contact should have at least one way of being '
                                                                 'contacted. Please select either email or phone, '
                                                                 'or both'],
                                        'contactable_by_phone': ['A contact should have at least one way '
                                                                 'of being contacted. Please select either '
                                                                 'email or phone, or both']}}
        assert response.json() == expected_response

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
