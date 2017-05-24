import pytest
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core import constants
from datahub.core.test_utils import LeelooTestCase
from .factories import CompanyFactory, ContactFactory

# mark the whole module for db use
pytestmark = pytest.mark.django_db


# V1

class AddContactV1TestCase(LeelooTestCase):
    """Add contact test case."""

    @freeze_time('2017-04-18 13:25:30.986208+00:00')
    def test_with_address_same_as_company(self):
        """Test add new contact with same address as company."""
        url = reverse('api-v1:contact-list')
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
            'adviser': str(self.user.pk),
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
        url = reverse('api-v1:contact-list')
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
        url = reverse('api-v1:contact-list')
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
        url = reverse('api-v1:contact-list')
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
        url = reverse('api-v1:contact-list')
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
        url = reverse('api-v1:contact-list')
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
        """Test contact preferences.

        At least one contact preference has to be True, this tests
        that if all are set to False, it fails.
        """
        url = reverse('api-v1:contact-list')
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


class EditContactV1TestCase(LeelooTestCase):
    """Edit contact test case."""

    def test_edit(self):
        """Test that it successfully edits an existing contact."""
        contact = ContactFactory(first_name='Foo')
        url = reverse('api-v1:contact-detail', kwargs={'pk': contact.pk})
        response = self.api_client.patch(url, {
            'first_name': 'bar',
        })

        assert response.status_code == status.HTTP_200_OK, response.data
        assert response.data['first_name'] == 'bar'


class ArchiveContactV1TestCase(LeelooTestCase):
    """Archive/unarchive contact test case."""

    def test_archive_without_reason(self):
        """Test archive contact without providing a reason."""
        contact = ContactFactory()
        url = reverse('api-v1:contact-archive', kwargs={'pk': contact.pk})
        response = self.api_client.post(url)

        assert response.data['archived']
        assert response.data['archived_reason'] == ''
        assert response.data['id'] == contact.pk

    def test_archive_with_reason(self):
        """Test archive contact providing a reason."""
        contact = ContactFactory()
        url = reverse('api-v1:contact-archive', kwargs={'pk': contact.pk})
        response = self.api_client.post(url, {'reason': 'foo'})

        assert response.data['archived']
        assert response.data['archived_reason'] == 'foo'
        assert response.data['id'] == contact.pk

    def test_unarchive(self):
        """Test unarchive contact."""
        contact = ContactFactory(archived=True, archived_reason='foo')
        url = reverse('api-v1:contact-unarchive', kwargs={'pk': contact.pk})
        response = self.api_client.get(url)

        assert not response.data['archived']
        assert response.data['archived_reason'] == ''
        assert response.data['id'] == contact.pk


class ViewContactV1TestCase(LeelooTestCase):
    """View contact test case."""

    def test_view(self):
        """Test view."""
        contact = ContactFactory()
        url = reverse('api-v1:contact-detail', kwargs={'pk': contact.pk})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == contact.pk


class ContactListV1TestCase(LeelooTestCase):
    """List/filter contacts test case."""

    def test_all(self):
        """Test getting all contacts"""
        ContactFactory.create_batch(5)

        url = reverse('api-v1:contact-list')
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 5


# V3

class AddContactV3TestCase(LeelooTestCase):
    """Add contact test case."""

    def test_with_manual_address(self):
        """Test add with manual address."""
        company = CompanyFactory()

        url = reverse('api-v3:contact:list')
        response = self.api_client.post(url, {
            'title': {
                'id': constants.Title.admiral_of_the_fleet.value.id
            },
            'first_name': 'Oratio',
            'last_name': 'Nelson',
            'job_title': constants.Role.owner.value.name,
            'company': {
                'id': company.pk
            },
            'email': 'foo@bar.com',
            'email_alternative': 'foo2@bar.com',
            'primary': True,
            'telephone_countrycode': '+44',
            'telephone_number': '123456789',
            'telephone_alternative': '987654321',
            'address_same_as_company': False,
            'address_1': 'Foo st.',
            'address_2': 'adr 2',
            'address_3': 'adr 3',
            'address_4': 'adr 4',
            'address_town': 'London',
            'address_county': 'London',
            'address_country': {
                'id': constants.Country.united_kingdom.value.id
            },
            'address_postcode': 'SW1A1AA',
            'notes': 'lorem ipsum',
            'contactable_by_dit': False,
            'contactable_by_dit_partners': False,
            'contactable_by_email': True,
            'contactable_by_phone': True
        }, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json() == {
            'id': response.json()['id'],
            'title': {
                'id': constants.Title.admiral_of_the_fleet.value.id,
                'name': constants.Title.admiral_of_the_fleet.value.name
            },
            'first_name': 'Oratio',
            'last_name': 'Nelson',
            'job_title': constants.Role.owner.value.name,
            'company': {
                'id': company.pk,
                'name': company.name
            },
            'adviser': {
                'id': str(self.user.pk),
                'first_name': self.user.first_name,
                'last_name': self.user.last_name
            },
            'email': 'foo@bar.com',
            'email_alternative': 'foo2@bar.com',
            'primary': True,
            'telephone_countrycode': '+44',
            'telephone_number': '123456789',
            'telephone_alternative': '987654321',
            'address_same_as_company': False,
            'address_1': 'Foo st.',
            'address_2': 'adr 2',
            'address_3': 'adr 3',
            'address_4': 'adr 4',
            'address_town': 'London',
            'address_county': 'London',
            'address_country': {
                'id': constants.Country.united_kingdom.value.id,
                'name': constants.Country.united_kingdom.value.name
            },
            'address_postcode': 'SW1A1AA',
            'notes': 'lorem ipsum',
            'contactable_by_dit': False,
            'contactable_by_dit_partners': False,
            'contactable_by_email': True,
            'contactable_by_phone': True,
            'archived': False,
            'archived_by': None,
            'archived_on': None,
            'archived_reason': None
        }

    @freeze_time('2017-04-18 13:25:30.986208+00:00')
    def test_with_address_same_as_company(self):
        """Test add new contact with same address as company."""
        url = reverse('api-v3:contact:list')
        response = self.api_client.post(url, {
            'first_name': 'Oratio',
            'last_name': 'Nelson',
            'company': {
                'id': CompanyFactory().pk
            },
            'email': 'foo@bar.com',
            'telephone_countrycode': '+44',
            'telephone_number': '123456789',
            'address_same_as_company': True,
            'primary': True
        }, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()

        assert response_data['address_same_as_company']
        assert not response_data['address_1']
        assert not response_data['address_2']
        assert not response_data['address_3']
        assert not response_data['address_4']
        assert not response_data['address_country']
        assert not response_data['address_county']
        assert not response_data['address_postcode']
        assert not response_data['address_town']

    def test_defaults(self):
        """Test defaults when adding an item."""
        url = reverse('api-v3:contact:list')
        response = self.api_client.post(url, {
            'first_name': 'Oratio',
            'last_name': 'Nelson',
            'company': {
                'id': CompanyFactory().pk
            },
            'email': 'foo@bar.com',
            'telephone_countrycode': '+44',
            'telephone_number': '123456789',
            'address_same_as_company': True,
            'primary': True
        }, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.data
        assert not response_data['title']
        assert not response_data['telephone_alternative']
        assert response_data['address_same_as_company']
        assert not response_data['email_alternative']
        assert not response_data['address_1']
        assert not response_data['address_2']
        assert not response_data['address_3']
        assert not response_data['address_4']
        assert not response_data['address_town']
        assert not response_data['address_county']
        assert not response_data['address_country']
        assert not response_data['address_postcode']
        assert not response_data['notes']
        assert not response_data['contactable_by_dit']
        assert not response_data['contactable_by_dit_partners']
        assert response_data['contactable_by_email']
        assert response_data['contactable_by_phone']

    def test_fails_with_invalid_email_address(self):
        """Test that fails if the email address is invalid."""
        url = reverse('api-v3:contact:list')
        response = self.api_client.post(url, {
            'first_name': 'Oratio',
            'last_name': 'Nelson',
            'company': {
                'id': CompanyFactory().pk
            },
            'email': 'invalid dot com',
            'telephone_countrycode': '+44',
            'telephone_number': '123456789',
            'address_same_as_company': True,
            'primary': True
        }, format='json')

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
            'company': {
                'id': CompanyFactory().pk
            },
            'email': 'foo@bar.com',
            'telephone_countrycode': '+44',
            'telephone_number': '123456789',
            'primary': True
        }, format='json')

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
            'company': {
                'id': CompanyFactory().pk
            },
            'email': 'foo@bar.com',
            'telephone_countrycode': '+44',
            'telephone_number': '123456789',
            'address_1': 'test',
            'primary': True
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['errors'] == {
            'address_country': ['This field may not be null.'],
            'address_town': ['This field may not be null.']
        }

    def test_fails_with_contact_preferences_not_set(self):
        """Test that fails without any contact preference."""
        url = reverse('api-v3:contact:list')
        response = self.api_client.post(url, {
            'first_name': 'Oratio',
            'last_name': 'Nelson',
            'company': {
                'id': CompanyFactory().pk
            },
            'email': 'foo@bar.com',
            'telephone_countrycode': '+44',
            'telephone_number': '123456789',
            'address_same_as_company': True,
            'contactable_by_email': False,
            'contactable_by_phone': False,
            'primary': True
        }, format='json')

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


class EditContactV3TestCase(LeelooTestCase):
    """Edit contact test case."""

    def test_patch(self):
        """Test that it successfully patch an existing contact."""
        company = CompanyFactory()

        contact = ContactFactory(
            title_id=constants.Title.admiral_of_the_fleet.value.id,
            first_name='Oratio',
            last_name='Nelson',
            job_title=constants.Role.owner.value.name,
            company=company,
            email='foo@bar.com',
            email_alternative='foo2@bar.com',
            primary=True,
            adviser=self.user,
            telephone_countrycode='+44',
            telephone_number='123456789',
            telephone_alternative='987654321',
            address_same_as_company=False,
            address_1='Foo st.',
            address_2='adr 2',
            address_3='adr 3',
            address_4='adr 4',
            address_town='London',
            address_county='London',
            address_country_id=constants.Country.united_kingdom.value.id,
            address_postcode='SW1A1AA',
            notes='lorem ipsum',
            contactable_by_dit=False,
            contactable_by_dit_partners=False,
            contactable_by_email=True,
            contactable_by_phone=True
        )

        url = reverse('api-v3:contact:detail', kwargs={'pk': contact.pk})
        response = self.api_client.patch(url, {
            'first_name': 'New Oratio',
        }, format='json')

        assert response.status_code == status.HTTP_200_OK, response.data
        assert response.json() == {
            'id': response.json()['id'],
            'title': {
                'id': constants.Title.admiral_of_the_fleet.value.id,
                'name': constants.Title.admiral_of_the_fleet.value.name
            },
            'first_name': 'New Oratio',
            'last_name': 'Nelson',
            'job_title': constants.Role.owner.value.name,
            'company': {
                'id': company.pk,
                'name': company.name
            },
            'email': 'foo@bar.com',
            'email_alternative': 'foo2@bar.com',
            'primary': True,
            'adviser': {
                'id': str(self.user.pk),
                'first_name': self.user.first_name,
                'last_name': self.user.last_name
            },
            'telephone_countrycode': '+44',
            'telephone_number': '123456789',
            'telephone_alternative': '987654321',
            'address_same_as_company': False,
            'address_1': 'Foo st.',
            'address_2': 'adr 2',
            'address_3': 'adr 3',
            'address_4': 'adr 4',
            'address_town': 'London',
            'address_county': 'London',
            'address_country': {
                'id': constants.Country.united_kingdom.value.id,
                'name': constants.Country.united_kingdom.value.name
            },
            'address_postcode': 'SW1A1AA',
            'notes': 'lorem ipsum',
            'contactable_by_dit': False,
            'contactable_by_dit_partners': False,
            'contactable_by_email': True,
            'contactable_by_phone': True,
            'archived': False,
            'archived_by': None,
            'archived_on': None,
            'archived_reason': None
        }


class ArchiveContactV3TestCase(LeelooTestCase):
    """Archive/unarchive contact test case."""

    def test_archive_without_reason(self):
        """Test archive contact without providing a reason."""
        contact = ContactFactory()
        url = reverse('api-v3:contact:archive', kwargs={'pk': contact.pk})
        response = self.api_client.post(url)

        assert response.data['archived']
        assert response.data['archived_by'] == {
            'id': str(self.user.pk),
            'first_name': self.user.first_name,
            'last_name': self.user.last_name
        }
        assert response.data['archived_reason'] == ''
        assert response.data['id'] == contact.pk

    def test_archive_with_reason(self):
        """Test archive contact providing a reason."""
        contact = ContactFactory()
        url = reverse('api-v3:contact:archive', kwargs={'pk': contact.pk})
        response = self.api_client.post(url, {'reason': 'foo'})

        assert response.data['archived']
        assert response.data['archived_by'] == {
            'id': str(self.user.pk),
            'first_name': self.user.first_name,
            'last_name': self.user.last_name
        }
        assert response.data['archived_reason'] == 'foo'
        assert response.data['id'] == contact.pk

    def test_unarchive(self):
        """Test unarchive contact."""
        contact = ContactFactory(archived=True, archived_reason='foo')
        url = reverse('api-v3:contact:unarchive', kwargs={'pk': contact.pk})
        response = self.api_client.get(url)

        assert not response.data['archived']
        assert not response.data['archived_by']
        assert response.data['archived_reason'] == ''
        assert response.data['id'] == contact.pk


class ViewContactV3TestCase(LeelooTestCase):
    """View contact test case."""

    def test_view(self):
        """Test view."""
        company = CompanyFactory()

        contact = ContactFactory(
            title_id=constants.Title.admiral_of_the_fleet.value.id,
            first_name='Oratio',
            last_name='Nelson',
            job_title=constants.Role.owner.value.name,
            company=company,
            email='foo@bar.com',
            email_alternative='foo2@bar.com',
            primary=True,
            adviser=self.user,
            telephone_countrycode='+44',
            telephone_number='123456789',
            telephone_alternative='987654321',
            address_same_as_company=False,
            address_1='Foo st.',
            address_2='adr 2',
            address_3='adr 3',
            address_4='adr 4',
            address_town='London',
            address_county='London',
            address_country_id=constants.Country.united_kingdom.value.id,
            address_postcode='SW1A1AA',
            notes='lorem ipsum',
            contactable_by_dit=False,
            contactable_by_dit_partners=False,
            contactable_by_email=True,
            contactable_by_phone=True
        )
        url = reverse('api-v3:contact:detail', kwargs={'pk': contact.pk})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'id': response.json()['id'],
            'title': {
                'id': constants.Title.admiral_of_the_fleet.value.id,
                'name': constants.Title.admiral_of_the_fleet.value.name
            },
            'first_name': 'Oratio',
            'last_name': 'Nelson',
            'job_title': constants.Role.owner.value.name,
            'company': {
                'id': company.pk,
                'name': company.name
            },
            'adviser': {
                'id': str(self.user.pk),
                'first_name': self.user.first_name,
                'last_name': self.user.last_name
            },
            'email': 'foo@bar.com',
            'email_alternative': 'foo2@bar.com',
            'primary': True,
            'telephone_countrycode': '+44',
            'telephone_number': '123456789',
            'telephone_alternative': '987654321',
            'address_same_as_company': False,
            'address_1': 'Foo st.',
            'address_2': 'adr 2',
            'address_3': 'adr 3',
            'address_4': 'adr 4',
            'address_town': 'London',
            'address_county': 'London',
            'address_country': {
                'id': constants.Country.united_kingdom.value.id,
                'name': constants.Country.united_kingdom.value.name
            },
            'address_postcode': 'SW1A1AA',
            'notes': 'lorem ipsum',
            'contactable_by_dit': False,
            'contactable_by_dit_partners': False,
            'contactable_by_email': True,
            'contactable_by_phone': True,
            'archived': False,
            'archived_by': None,
            'archived_on': None,
            'archived_reason': None
        }


class ContactListV3TestCase(LeelooTestCase):
    """List/filter contacts test case."""

    def test_all(self):
        """Test getting all contacts"""
        ContactFactory.create_batch(5)

        url = reverse('api-v3:contact:list')
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 5

    def test_filter_by_company(self):
        """Test getting contacts by company id"""
        company1 = CompanyFactory()
        company2 = CompanyFactory()

        ContactFactory.create_batch(3, company=company1)
        contacts = ContactFactory.create_batch(2, company=company2)

        url = '{}?company_id={}'.format(
            reverse('api-v3:contact:list'),
            company2.id
        )
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        assert {contact['id'] for contact in response.data['results']} == {contact.id for contact in contacts}
