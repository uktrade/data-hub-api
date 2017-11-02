from datetime import date

import pytest
import reversion
from django.utils.timezone import now
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse
from reversion.models import Version

from datahub.core import constants
from datahub.core.test_utils import APITestMixin, format_date_or_datetime
from .factories import CompanyFactory, ContactFactory

# mark the whole module for db use
pytestmark = pytest.mark.django_db


class TestAddContact(APITestMixin):
    """Add contact test case."""

    @freeze_time('2017-04-18 13:25:30.986208')
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
                'id': str(company.pk)
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
            'address_town': 'London',
            'address_county': 'London',
            'address_country': {
                'id': constants.Country.united_kingdom.value.id
            },
            'address_postcode': 'SW1A1AA',
            'notes': 'lorem ipsum',
            'contactable_by_dit': True,
            'contactable_by_uk_dit_partners': True,
            'contactable_by_overseas_dit_partners': True,
            'accepts_dit_email_marketing': True,
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
                'id': str(company.pk),
                'name': company.name
            },
            'adviser': {
                'id': str(self.user.pk),
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'name': self.user.name
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
            'address_town': 'London',
            'address_county': 'London',
            'address_country': {
                'id': constants.Country.united_kingdom.value.id,
                'name': constants.Country.united_kingdom.value.name
            },
            'address_postcode': 'SW1A1AA',
            'notes': 'lorem ipsum',
            'contactable_by_dit': True,
            'contactable_by_uk_dit_partners': True,
            'contactable_by_overseas_dit_partners': True,
            'accepts_dit_email_marketing': True,
            'contactable_by_email': True,
            'contactable_by_phone': True,
            'archived': False,
            'archived_by': None,
            'archived_on': None,
            'archived_reason': None,
            'created_on': '2017-04-18T13:25:30.986208Z',
            'modified_on': '2017-04-18T13:25:30.986208Z',
        }

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
        assert not response_data['address_town']
        assert not response_data['address_county']
        assert not response_data['address_country']
        assert not response_data['address_postcode']
        assert not response_data['notes']
        assert not response_data['contactable_by_dit']
        assert not response_data['contactable_by_uk_dit_partners']
        assert not response_data['contactable_by_overseas_dit_partners']
        assert not response_data['accepts_dit_email_marketing']
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
        assert response.data == {
            'address_same_as_company': [
                'Please select either address_same_as_company or enter an address manually.'
            ]
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
        assert response.data == {
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
        assert response.data == {
            'contactable_by_email': [
                'A contact should have at least one way of being contacted. '
                'Please select either email or phone, or both'
            ],
            'contactable_by_phone': [
                'A contact should have at least one way of being contacted. '
                'Please select either email or phone, or both'
            ]
        }

    def test_fails_without_primary_specified(self):
        """Test that fails if primary is not specified."""
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
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {
            'primary': ['This field is required.']
        }


class TestEditContact(APITestMixin):
    """Edit contact test case."""

    def test_patch(self):
        """Test that it successfully patch an existing contact."""
        with freeze_time('2017-04-18 13:25:30.986208'):
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
                address_town='London',
                address_county='London',
                address_country_id=constants.Country.united_kingdom.value.id,
                address_postcode='SW1A1AA',
                notes='lorem ipsum',
                contactable_by_dit=False,
                contactable_by_uk_dit_partners=False,
                contactable_by_overseas_dit_partners=False,
                accepts_dit_email_marketing=False,
                contactable_by_email=True,
                contactable_by_phone=True
            )

        url = reverse('api-v3:contact:detail', kwargs={'pk': contact.pk})
        with freeze_time('2017-04-19 13:25:30.986208'):
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
                'id': str(company.pk),
                'name': company.name
            },
            'email': 'foo@bar.com',
            'email_alternative': 'foo2@bar.com',
            'primary': True,
            'adviser': {
                'id': str(self.user.pk),
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'name': self.user.name
            },
            'telephone_countrycode': '+44',
            'telephone_number': '123456789',
            'telephone_alternative': '987654321',
            'address_same_as_company': False,
            'address_1': 'Foo st.',
            'address_2': 'adr 2',
            'address_town': 'London',
            'address_county': 'London',
            'address_country': {
                'id': constants.Country.united_kingdom.value.id,
                'name': constants.Country.united_kingdom.value.name
            },
            'address_postcode': 'SW1A1AA',
            'notes': 'lorem ipsum',
            'contactable_by_dit': False,
            'contactable_by_uk_dit_partners': False,
            'contactable_by_overseas_dit_partners': False,
            'accepts_dit_email_marketing': False,
            'contactable_by_email': True,
            'contactable_by_phone': True,
            'archived': False,
            'archived_by': None,
            'archived_on': None,
            'archived_reason': None,
            'created_on': '2017-04-18T13:25:30.986208Z',
            'modified_on': '2017-04-19T13:25:30.986208Z',
        }


class TestArchiveContact(APITestMixin):
    """Archive/unarchive contact test case."""

    def test_archive_without_reason(self):
        """Test archive contact without providing a reason."""
        contact = ContactFactory()
        url = reverse('api-v3:contact:archive', kwargs={'pk': contact.pk})
        response = self.api_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {
            'reason': ['This field is required.']
        }

    def test_archive_with_reason(self):
        """Test archive contact providing a reason."""
        contact = ContactFactory()
        url = reverse('api-v3:contact:archive', kwargs={'pk': contact.pk})
        response = self.api_client.post(url, {'reason': 'foo'})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['archived']
        assert response.data['archived_by'] == {
            'id': str(self.user.pk),
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'name': self.user.name
        }
        assert response.data['archived_reason'] == 'foo'
        assert response.data['id'] == str(contact.pk)

    def test_unarchive(self):
        """Test unarchiving a contact."""
        contact = ContactFactory(archived=True, archived_reason='foo')
        url = reverse('api-v3:contact:unarchive', kwargs={'pk': contact.pk})
        response = self.api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert not response.data['archived']
        assert not response.data['archived_by']
        assert response.data['archived_reason'] == ''
        assert response.data['id'] == str(contact.pk)

    def test_unarchive_wrong_method(self):
        """Tests that GET requests to the unarchive endpoint fail."""
        contact = ContactFactory(archived=True, archived_reason='foo')
        url = reverse('api-v3:contact:unarchive', kwargs={'pk': contact.pk})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


class TestViewContact(APITestMixin):
    """View contact test case."""

    @freeze_time('2017-04-18 13:25:30.986208')
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
            address_town='London',
            address_county='London',
            address_country_id=constants.Country.united_kingdom.value.id,
            address_postcode='SW1A1AA',
            notes='lorem ipsum',
            contactable_by_dit=False,
            contactable_by_uk_dit_partners=False,
            contactable_by_overseas_dit_partners=False,
            accepts_dit_email_marketing=False,
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
                'id': str(company.pk),
                'name': company.name
            },
            'adviser': {
                'id': str(self.user.pk),
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'name': self.user.name
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
            'address_town': 'London',
            'address_county': 'London',
            'address_country': {
                'id': constants.Country.united_kingdom.value.id,
                'name': constants.Country.united_kingdom.value.name
            },
            'address_postcode': 'SW1A1AA',
            'notes': 'lorem ipsum',
            'contactable_by_dit': False,
            'contactable_by_uk_dit_partners': False,
            'contactable_by_overseas_dit_partners': False,
            'accepts_dit_email_marketing': False,
            'contactable_by_email': True,
            'contactable_by_phone': True,
            'archived': False,
            'archived_by': None,
            'archived_on': None,
            'archived_reason': None,
            'created_on': '2017-04-18T13:25:30.986208Z',
            'modified_on': '2017-04-18T13:25:30.986208Z',
        }


class TestContactList(APITestMixin):
    """List/filter contacts test case."""

    def test_all(self):
        """Test getting all contacts"""
        ContactFactory.create_batch(5)

        url = reverse('api-v3:contact:list')
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 5

    def test_contacts_are_sorted_by_created_on_desc(self):
        """Test contacts are sorted by created on desc."""
        datetimes = [date(year, 1, 1) for year in range(2015, 2030)]
        contacts = []

        for creation_datetime in datetimes:
            with freeze_time(creation_datetime):
                contacts.append(
                    ContactFactory()
                )

        url = reverse('api-v3:contact:list')
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == len(contacts)
        response_data = response.json()['results']

        contacts = sorted(contacts, key=lambda key: key.created_on, reverse=True)
        contact_ids = [str(contact.id) for contact in contacts]
        assert [contact['id'] for contact in response_data] == contact_ids

    def test_filter_by_company(self):
        """Test getting contacts by company id"""
        company1 = CompanyFactory()
        company2 = CompanyFactory()

        ContactFactory.create_batch(3, company=company1)
        contacts = ContactFactory.create_batch(2, company=company2)

        url = reverse('api-v3:contact:list')
        response = self.api_client.get(url, {'company_id': company2.id})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        expected_contacts = {str(contact.id) for contact in contacts}
        assert {contact['id'] for contact in response.data['results']} == expected_contacts


class TestAuditLogView(APITestMixin):
    """Tests for the audit log view."""

    def test_audit_log_view(self):
        """Test retrieval of audit log."""
        initial_datetime = now()
        with reversion.create_revision():
            contact = ContactFactory(
                notes='Initial notes',
            )

            reversion.set_comment('Initial')
            reversion.set_date_created(initial_datetime)
            reversion.set_user(self.user)

        changed_datetime = now()
        with reversion.create_revision():
            contact.notes = 'New notes'
            contact.save()

            reversion.set_comment('Changed')
            reversion.set_date_created(changed_datetime)
            reversion.set_user(self.user)

        versions = Version.objects.get_for_object(contact)
        version_id = versions[0].id
        url = reverse('api-v3:contact:audit-item', kwargs={'pk': contact.pk})

        response = self.api_client.get(url)
        response_data = response.json()['results']

        # No need to test the whole response
        assert len(response_data) == 1
        entry = response_data[0]

        assert entry['id'] == version_id
        assert entry['user']['name'] == self.user.name
        assert entry['comment'] == 'Changed'
        assert entry['timestamp'] == format_date_or_datetime(changed_datetime)
        assert entry['changes']['notes'] == ['Initial notes', 'New notes']
        assert not {'created_on', 'created_by', 'modified_on', 'modified_by'} & entry[
            'changes'].keys()
