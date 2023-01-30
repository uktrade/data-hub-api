from datetime import date

import factory
import pytest
import reversion
from django.conf import settings
from django.utils.timezone import now
from freezegun import freeze_time
from requests.exceptions import ConnectionError, ConnectTimeout, ReadTimeout
from rest_framework import status
from rest_framework.reverse import reverse
from reversion.models import Version

from datahub.company.consent import CONSENT_SERVICE_PERSON_PATH_LOOKUP
from datahub.company.constants import (
    CONSENT_SERVICE_EMAIL_CONSENT_TYPE,
)
from datahub.company.models import Contact
from datahub.company.test.factories import ArchivedContactFactory, CompanyFactory, ContactFactory
from datahub.core import constants
from datahub.core.reversion import EXCLUDED_BASE_MODEL_FIELDS
from datahub.core.test_utils import (
    APITestMixin,
    create_test_user,
    format_date_or_datetime,
    HawkMockJSONResponse,
)
from datahub.metadata.test.factories import TeamFactory

# mark the whole module for db use
pytestmark = pytest.mark.django_db


def generate_hawk_response(response):
    """Mocks HAWK server validation for content."""
    return HawkMockJSONResponse(
        api_id=settings.COMPANY_MATCHING_HAWK_ID,
        api_key=settings.COMPANY_MATCHING_HAWK_KEY,
        response=response,
    )


@pytest.fixture
def get_consent_fixture(requests_mock):
    """Mock get call to consent service."""
    yield lambda response: requests_mock.get(
        f'{settings.CONSENT_SERVICE_BASE_URL}'
        f'{CONSENT_SERVICE_PERSON_PATH_LOOKUP}',
        status_code=200,
        text=generate_hawk_response(response),
    )


class AddContactBase(APITestMixin):
    """Add contact test case."""

    endpoint_namespace = None

    @freeze_time('2017-04-18 13:25:30.986208')
    def test_with_manual_address(self, get_consent_fixture):
        """Test add with manual address."""
        company = CompanyFactory()
        get_consent_fixture({
            'results': [
                {
                    'consents': [
                        'email_marketing',
                    ],
                    'email': 'foo@bar.com',
                },
            ],
        })
        url = reverse(f'{self.endpoint_namespace}:contact:list')
        response = self.api_client.post(
            url,
            data={
                'title': {
                    'id': constants.Title.admiral_of_the_fleet.value.id,
                },
                'first_name': 'Oratio',
                'last_name': 'Nelson',
                'job_title': 'Head of Sales',
                'company': {
                    'id': str(company.pk),
                },
                'email': 'FOO@bar.com',
                'primary': True,
                'full_telephone_number': '+44 123456789',
                'address_same_as_company': False,
                'address_1': 'Foo st.',
                'address_2': 'adr 2',
                'address_town': 'London',
                'address_county': 'London',
                'address_country': {
                    'id': constants.Country.united_kingdom.value.id,
                },
                'address_postcode': 'SW1A1AA',
                'notes': 'lorem ipsum',
                'accepts_dit_email_marketing': True,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json() == {
            'id': response.json()['id'],
            'title': {
                'id': constants.Title.admiral_of_the_fleet.value.id,
                'name': constants.Title.admiral_of_the_fleet.value.name,
            },
            'first_name': 'Oratio',
            'last_name': 'Nelson',
            'name': 'Oratio Nelson',
            'job_title': 'Head of Sales',
            'company': {
                'id': str(company.pk),
                'name': company.name,
            },
            'adviser': {
                'id': str(self.user.pk),
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'name': self.user.name,
            },
            'email': 'foo@bar.com',
            'primary': True,
            'full_telephone_number': '+44 123456789',
            'address_same_as_company': False,
            'address_1': 'Foo st.',
            'address_2': 'adr 2',
            'address_area': None,
            'address_town': 'London',
            'address_county': 'London',
            'address_country': {
                'id': constants.Country.united_kingdom.value.id,
                'name': constants.Country.united_kingdom.value.name,
            },
            'address_postcode': 'SW1A1AA',
            'notes': 'lorem ipsum',
            'accepts_dit_email_marketing': True,
            'archived': False,
            'archived_by': None,
            'archived_documents_url_path': '',
            'archived_on': None,
            'archived_reason': None,
            'created_on': '2017-04-18T13:25:30.986208Z',
            'modified_on': '2017-04-18T13:25:30.986208Z',
        }

    def test_with_address_same_as_company(self):
        """Test add new contact with same address as company."""
        url = reverse(f'{self.endpoint_namespace}:contact:list')
        response = self.api_client.post(
            url,
            data={
                'first_name': 'Oratio',
                'last_name': 'Nelson',
                'company': {
                    'id': CompanyFactory().pk,
                },
                'email': 'foo@bar.com',
                'address_same_as_company': True,
                'primary': True,
            },
        )

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
        url = reverse(f'{self.endpoint_namespace}:contact:list')
        response = self.api_client.post(
            url,
            data={
                'first_name': 'Oratio',
                'last_name': 'Nelson',
                'company': {
                    'id': CompanyFactory().pk,
                },
                'email': 'foo@bar.com',
                'address_same_as_company': True,
                'primary': True,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.data
        assert not response_data['title']
        assert response_data['address_same_as_company']
        assert not response_data['address_1']
        assert not response_data['address_2']
        assert not response_data['address_town']
        assert not response_data['address_county']
        assert not response_data['address_country']
        assert not response_data['address_postcode']
        assert not response_data['notes']
        assert not response_data['accepts_dit_email_marketing']

    def test_fails_with_invalid_email_address(self):
        """Test that fails if the email address is invalid."""
        url = reverse(f'{self.endpoint_namespace}:contact:list')
        response = self.api_client.post(
            url,
            data={
                'first_name': 'Oratio',
                'last_name': 'Nelson',
                'company': {
                    'id': CompanyFactory().pk,
                },
                'email': 'invalid dot com',
                'address_same_as_company': True,
                'primary': True,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {
            'email': ['Enter a valid email address.'],
        }

    def test_fails_without_address(self):
        """Test that fails without any address."""
        url = reverse(f'{self.endpoint_namespace}:contact:list')
        response = self.api_client.post(
            url,
            data={
                'first_name': 'Oratio',
                'last_name': 'Nelson',
                'company': {
                    'id': CompanyFactory().pk,
                },
                'email': 'foo@bar.com',
                'primary': True,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {
            'address_same_as_company': [
                'Please select either address_same_as_company or enter an address manually.',
            ],
        }

    def test_fails_with_only_partial_manual_address(self):
        """Test that fails if only partial manual address supplied."""
        url = reverse(f'{self.endpoint_namespace}:contact:list')
        response = self.api_client.post(
            url,
            data={
                'first_name': 'Oratio',
                'last_name': 'Nelson',
                'company': {
                    'id': CompanyFactory().pk,
                },
                'email': 'foo@bar.com',
                'address_1': 'test',
                'primary': True,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {
            'address_country': ['This field is required.'],
            'address_town': ['This field is required.'],
        }

    def test_fails_without_primary_specified(self):
        """Test that fails if primary is not specified."""
        url = reverse(f'{self.endpoint_namespace}:contact:list')
        response = self.api_client.post(
            url,
            data={
                'first_name': 'Oratio',
                'last_name': 'Nelson',
                'company': {
                    'id': CompanyFactory().pk,
                },
                'email': 'foo@bar.com',
                'address_same_as_company': True,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {
            'primary': ['This field is required.'],
        }

    def test_duplicate_emails_ok_for_different_company(self):
        """It should be ok to save a non unique email if the company is different."""
        company_1 = CompanyFactory(name='Company ABC')
        company_2 = CompanyFactory(name='Company XYZ')
        email = 'foo@bar.com'
        ContactFactory(company=company_1, email=email)
        url = reverse(f'{self.endpoint_namespace}:contact:list')
        response = self.api_client.post(
            url,
            data={
                'primary': False,
                'first_name': 'Oratio',
                'last_name': 'Nelson',
                'company': {
                    'id': company_2.pk,
                },
                'email': email,
                'address_same_as_company': True,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data['first_name'] == 'Oratio'
        assert response_data['last_name'] == 'Nelson'
        assert response_data['company']['id'] == str(company_2.id)

    def test_no_duplicate_emails_for_company(self):
        """Validation error should occur when the email address is not unique at the company."""
        company_name = 'Test House'
        company = CompanyFactory(name=company_name)
        email = 'foo@bar.com'
        ContactFactory(company=company, email=email)
        url = reverse(f'{self.endpoint_namespace}:contact:list')
        response = self.api_client.post(
            url,
            data={
                'primary': False,
                'first_name': 'Oratio',
                'last_name': 'Nelson',
                'company': {
                    'id': company.pk,
                },
                'email': email,
                'address_same_as_company': True,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {
            'email': [f'A contact with this email already exists at {company_name}.'],
        }


class TestAddContactV3(AddContactBase):
    """Test v3 of the contact adding endpoint"""

    endpoint_namespace = 'api-v3'


class TestAddContactV4(AddContactBase):
    """Test v4 of the contact adding endpoint"""

    endpoint_namespace = 'api-v4'

    @freeze_time('2017-04-18 13:25:30.986208')
    def test_with_us_manual_address(self, get_consent_fixture):
        """Test add with manual address."""
        company = CompanyFactory()
        get_consent_fixture({
            'results': [
                {
                    'consents': [
                        'email_marketing',
                    ],
                    'email': 'foo@bar.com',
                },
            ],
        })
        url = reverse('api-v4:contact:list')
        response = self.api_client.post(
            url,
            data={
                'title': {
                    'id': constants.Title.admiral_of_the_fleet.value.id,
                },
                'first_name': 'Oratio',
                'last_name': 'Nelson',
                'job_title': 'Head of Sales',
                'company': {
                    'id': str(company.pk),
                },
                'email': 'foo@bar.com',
                'primary': True,
                'full_telephone_number': '+44 123456789',
                'address_same_as_company': False,
                'address_1': 'Foo st.',
                'address_2': 'adr 2',
                'address_town': 'Brooklyn',
                'address_county': '',
                'address_country': {
                    'id': constants.Country.united_states.value.id,
                    'name': constants.Country.united_states.value.name,
                },
                'address_area': {
                    'id': constants.AdministrativeArea.new_york.value.id,
                    'name': constants.AdministrativeArea.new_york.value.name,
                },
                'address_postcode': 'SW1A1AA',
                'notes': 'lorem ipsum',
                'accepts_dit_email_marketing': True,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json() == {
            'id': response.json()['id'],
            'title': {
                'id': constants.Title.admiral_of_the_fleet.value.id,
                'name': constants.Title.admiral_of_the_fleet.value.name,
            },
            'first_name': 'Oratio',
            'last_name': 'Nelson',
            'name': 'Oratio Nelson',
            'job_title': 'Head of Sales',
            'company': {
                'id': str(company.pk),
                'name': company.name,
            },
            'adviser': {
                'id': str(self.user.pk),
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'name': self.user.name,
            },
            'email': 'foo@bar.com',
            'primary': True,
            'full_telephone_number': '+44 123456789',
            'address_same_as_company': False,
            'address_1': 'Foo st.',
            'address_2': 'adr 2',
            'address_town': 'Brooklyn',
            'address_county': '',
            'address_country': {
                'id': constants.Country.united_states.value.id,
                'name': constants.Country.united_states.value.name,
            },
            'address_area': {
                'id': constants.AdministrativeArea.new_york.value.id,
                'name': constants.AdministrativeArea.new_york.value.name,
            },
            'address_postcode': 'SW1A1AA',
            'notes': 'lorem ipsum',
            'accepts_dit_email_marketing': True,
            'archived': False,
            'archived_by': None,
            'archived_documents_url_path': '',
            'archived_on': None,
            'archived_reason': None,
            'created_on': '2017-04-18T13:25:30.986208Z',
            'modified_on': '2017-04-18T13:25:30.986208Z',
        }

    def test_fails_with_us_but_no_area(self):
        """Test that fails if only partial manual address supplied."""
        url = reverse('api-v4:contact:list')
        response = self.api_client.post(
            url,
            data={
                'first_name': 'Oratio',
                'last_name': 'Nelson',
                'company': {
                    'id': CompanyFactory().pk,
                },
                'email': 'foo@bar.com',
                'full_telephone_number': '+44 123456789',
                'address_country': {
                    'id': constants.Country.united_states.value.id,
                    'name': constants.Country.united_states.value.name,
                },
                'address_1': 'line 1',
                'address_2': 'line 2',
                'address_area': None,
                'address_town': 'town',
                'primary': True,
            },
        )

        assert response.data == {
            'address_area': [
                'This field is required.',
            ],
        }
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class EditContactBase(APITestMixin):
    """Edit contact test case."""

    endpoint_namespace = None

    def test_patch(self):
        """Test that it successfully patches an existing contact."""
        with freeze_time('2017-04-18 13:25:30.986208'):
            company = CompanyFactory()

            contact = ContactFactory(
                title_id=constants.Title.admiral_of_the_fleet.value.id,
                first_name='Oratio',
                last_name='Nelson',
                job_title='Head of Sales',
                company=company,
                email='foo@bar.com',
                primary=True,
                adviser=self.user,
                full_telephone_number='+44 123456789',
                address_same_as_company=False,
                address_1='Foo st.',
                address_2='adr 2',
                address_town='London',
                address_county='London',
                address_country_id=constants.Country.united_kingdom.value.id,
                address_postcode='SW1A1AA',
                notes='lorem ipsum',
            )

        url = reverse(f'{self.endpoint_namespace}:contact:detail', kwargs={'pk': contact.pk})
        with freeze_time('2017-04-19 13:25:30.986208'):
            response = self.api_client.patch(
                url,
                data={
                    'first_name': 'New Oratio',
                },
            )

        assert response.status_code == status.HTTP_200_OK, response.data
        assert response.json() == {
            'id': response.json()['id'],
            'title': {
                'id': constants.Title.admiral_of_the_fleet.value.id,
                'name': constants.Title.admiral_of_the_fleet.value.name,
            },
            'first_name': 'New Oratio',
            'last_name': 'Nelson',
            'name': 'New Oratio Nelson',
            'job_title': 'Head of Sales',
            'company': {
                'id': str(company.pk),
                'name': company.name,
            },
            'email': 'foo@bar.com',
            'primary': True,
            'adviser': {
                'id': str(self.user.pk),
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'name': self.user.name,
            },
            'full_telephone_number': '+44 123456789',
            'address_same_as_company': False,
            'address_1': 'Foo st.',
            'address_2': 'adr 2',
            'address_area': None,
            'address_town': 'London',
            'address_county': 'London',
            'address_country': {
                'id': constants.Country.united_kingdom.value.id,
                'name': constants.Country.united_kingdom.value.name,
            },
            'address_postcode': 'SW1A1AA',
            'notes': 'lorem ipsum',
            'accepts_dit_email_marketing': False,
            'archived': False,
            'archived_by': None,
            'archived_documents_url_path': contact.archived_documents_url_path,
            'archived_on': None,
            'archived_reason': None,
            'created_on': '2017-04-18T13:25:30.986208Z',
            'modified_on': '2017-04-19T13:25:30.986208Z',
        }

    def test_cannot_update_if_archived(self):
        """Test that an archived contact cannot be updated."""
        company = ArchivedContactFactory()

        url = reverse(f'{self.endpoint_namespace}:contact:detail', kwargs={'pk': company.pk})
        response = self.api_client.patch(
            url,
            data={
                'first_name': 'new name',
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'non_field_errors': ['This record has been archived and cannot be edited.'],
        }

    def test_update_read_only_fields(self):
        """Test updating read-only fields."""
        contact = ContactFactory(
            archived_documents_url_path='old_path',
        )

        url = reverse(f'{self.endpoint_namespace}:contact:detail', kwargs={'pk': contact.pk})
        response = self.api_client.patch(
            url,
            data={
                'archived_documents_url_path': 'new_path',
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['archived_documents_url_path'] == 'old_path'

    def test_unchanged_email_ok(self):
        """If the email has not changed, it should not raise a validation error."""
        company_name = 'Test House'
        company = CompanyFactory(name=company_name)
        email = 'foo@bar.com'
        contact = ContactFactory(company=company, email=email)
        url = reverse(f'{self.endpoint_namespace}:contact:detail', kwargs={'pk': contact.pk})
        response = self.api_client.patch(
            url,
            data={
                'first_name': 'Oratio',
                'company': {
                    'id': company.pk,
                },
                'email': email,
            },
        )

        assert response.status_code == status.HTTP_200_OK

    def test_duplicate_email_at_company_from_payload(self):
        """Error if another contact at the company specified in payload has the email."""
        company_name = 'Test House'
        company = CompanyFactory(name=company_name)
        email = 'contact1@example.com'
        ContactFactory(company=company, email=email)
        contact = ContactFactory(company=company, email='contact2@example.com')
        url = reverse(f'{self.endpoint_namespace}:contact:detail', kwargs={'pk': contact.pk})
        response = self.api_client.patch(
            url,
            data={
                'first_name': 'Oratio',
                'company': {
                    'id': company.pk,
                },
                'email': email,
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {
            'email': [f'A contact with this email already exists at {company_name}.'],
        }

    def test_duplicate_email_at_company_from_database(self):
        """Error if another contact at the company in the db has the same email."""
        company_name = 'Test House'
        company = CompanyFactory(name=company_name)
        email = 'contact1@example.com'
        ContactFactory(company=company, email=email)
        contact = ContactFactory(company=company, email='contact2@example.com')
        url = reverse(f'{self.endpoint_namespace}:contact:detail', kwargs={'pk': contact.pk})
        response = self.api_client.patch(
            url,
            data={
                'first_name': 'Oratio',
                'email': email,
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {
            'email': [f'A contact with this email already exists at {company_name}.'],
        }


class TestEditContactV3(EditContactBase):
    """Test case for v3 of the edit contacts endpoint"""

    endpoint_namespace = 'api-v3'


class TestEditContactV4(EditContactBase):
    """Test case for v4 of the edit contacts endpoint"""

    endpoint_namespace = 'api-v4'

    def test_patch_area(self):
        """Test that it successfully patch an existing contact."""
        with freeze_time('2017-04-18 13:25:30.986208'):
            company = CompanyFactory()

            contact = ContactFactory(
                title_id=constants.Title.admiral_of_the_fleet.value.id,
                first_name='Oratio',
                last_name='Nelson',
                job_title='Head of Sales',
                company=company,
                email='foo@bar.com',
                primary=True,
                adviser=self.user,
                full_telephone_number='+44 123456789',
                address_same_as_company=False,
                address_1='Foo st.',
                address_2='adr 2',
                address_town='London',
                address_county='London',
                address_country_id=constants.Country.united_states.value.id,
                address_postcode='SW1A1AA',
                notes='lorem ipsum',
            )

        url = reverse(f'{self.endpoint_namespace}:contact:detail', kwargs={'pk': contact.pk})
        with freeze_time('2017-04-19 13:25:30.986208'):
            response = self.api_client.patch(
                url,
                data={
                    'address_area': {
                        'id': constants.AdministrativeArea.new_york.value.id,
                        'name': constants.AdministrativeArea.new_york.value.name,
                    },
                },
            )

        assert response.status_code == status.HTTP_200_OK, response.data
        assert response.json() == {
            'id': response.json()['id'],
            'title': {
                'id': constants.Title.admiral_of_the_fleet.value.id,
                'name': constants.Title.admiral_of_the_fleet.value.name,
            },
            'first_name': 'Oratio',
            'last_name': 'Nelson',
            'name': 'Oratio Nelson',
            'job_title': 'Head of Sales',
            'company': {
                'id': str(company.pk),
                'name': company.name,
            },
            'email': 'foo@bar.com',
            'primary': True,
            'adviser': {
                'id': str(self.user.pk),
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'name': self.user.name,
            },
            'full_telephone_number': '+44 123456789',
            'address_same_as_company': False,
            'address_1': 'Foo st.',
            'address_2': 'adr 2',
            'address_town': 'London',
            'address_county': 'London',
            'address_country': {
                'id': constants.Country.united_states.value.id,
                'name': constants.Country.united_states.value.name,
            },
            'address_area': {
                'id': constants.AdministrativeArea.new_york.value.id,
                'name': constants.AdministrativeArea.new_york.value.name,
            },
            'address_postcode': 'SW1A1AA',
            'notes': 'lorem ipsum',
            'accepts_dit_email_marketing': False,
            'archived': False,
            'archived_by': None,
            'archived_documents_url_path': contact.archived_documents_url_path,
            'archived_on': None,
            'archived_reason': None,
            'created_on': '2017-04-18T13:25:30.986208Z',
            'modified_on': '2017-04-19T13:25:30.986208Z',
        }

    def test_try_to_remove_area(self):
        """Test that it successfully patch an existing contact."""
        with freeze_time('2017-04-18 13:25:30.986208'):
            company = CompanyFactory()

            contact = ContactFactory(
                title_id=constants.Title.admiral_of_the_fleet.value.id,
                first_name='Oratio',
                last_name='Nelson',
                job_title='Head of Sales',
                company=company,
                email='foo@bar.com',
                primary=True,
                adviser=self.user,
                address_same_as_company=False,
                address_1='Foo st.',
                address_2='adr 2',
                address_town='London',
                address_county='London',
                address_area_id=constants.AdministrativeArea.new_york.value.id,
                address_country_id=constants.Country.united_states.value.id,
                address_postcode='SW1A1AA',
                notes='lorem ipsum',
            )

        url = reverse(f'{self.endpoint_namespace}:contact:detail', kwargs={'pk': contact.pk})
        with freeze_time('2017-04-19 13:25:30.986208'):
            response = self.api_client.patch(
                url,
                data={
                    'address_area': None,
                },
            )

        assert response.status_code == status.HTTP_400_BAD_REQUEST, response.data
        assert response.json() == {
            'address_area': ['This field is required.'],
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
            'reason': ['This field is required.'],
        }

    def test_archive_with_reason(self):
        """Test archive contact providing a reason."""
        contact = ContactFactory()
        url = reverse('api-v3:contact:archive', kwargs={'pk': contact.pk})
        response = self.api_client.post(url, data={'reason': 'foo'})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['archived']
        assert response.data['archived_by'] == {
            'id': str(self.user.pk),
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'name': self.user.name,
        }
        assert response.data['archived_reason'] == 'foo'
        assert response.data['id'] == str(contact.pk)

    def test_archive_with_invalid_address(self):
        """Test archiving a contact with an invalid address."""
        contact = ContactFactory(
            address_same_as_company=False,
            address_1='',
        )
        url = reverse('api-v3:contact:archive', kwargs={'pk': contact.pk})
        response = self.api_client.post(url, data={'reason': 'foo'})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['archived']

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


class ViewContactBase(APITestMixin):
    """View contact test case."""

    endpoint_namespace = None

    @freeze_time('2017-04-18 13:25:30.986208')
    def test_view(self):
        """Test view."""
        company = CompanyFactory()

        contact = ContactFactory(
            title_id=constants.Title.admiral_of_the_fleet.value.id,
            first_name='Oratio',
            last_name='Nelson',
            job_title='Head of Sales',
            company=company,
            email='foo@bar.com',
            primary=True,
            adviser=self.user,
            full_telephone_number='+1 123456789',
            address_same_as_company=False,
            address_1='Foo st.',
            address_2='adr 2',
            address_town='Baytown',
            address_county='Houston',
            address_area_id=constants.AdministrativeArea.texas.value.id,
            address_country_id=constants.Country.united_states.value.id,
            address_postcode='YO22 4JU',
            notes='lorem ipsum',
        )
        url = reverse(f'{self.endpoint_namespace}:contact:detail', kwargs={'pk': contact.pk})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'id': response.json()['id'],
            'title': {
                'id': constants.Title.admiral_of_the_fleet.value.id,
                'name': constants.Title.admiral_of_the_fleet.value.name,
            },
            'first_name': 'Oratio',
            'last_name': 'Nelson',
            'name': 'Oratio Nelson',
            'job_title': 'Head of Sales',
            'company': {
                'id': str(company.pk),
                'name': company.name,
            },
            'adviser': {
                'id': str(self.user.pk),
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'name': self.user.name,
            },
            'email': 'foo@bar.com',
            'primary': True,
            'full_telephone_number': '+1 123456789',
            'address_same_as_company': False,
            'address_1': 'Foo st.',
            'address_2': 'adr 2',
            'address_town': 'Baytown',
            'address_county': 'Houston',
            'address_country': {
                'id': constants.Country.united_states.value.id,
                'name': constants.Country.united_states.value.name,
            },
            'address_area': {
                'id': constants.AdministrativeArea.texas.value.id,
                'name': constants.AdministrativeArea.texas.value.name,
            },
            'address_postcode': 'YO22 4JU',
            'notes': 'lorem ipsum',
            'accepts_dit_email_marketing': False,
            'archived': False,
            'archived_by': None,
            'archived_documents_url_path': contact.archived_documents_url_path,
            'archived_on': None,
            'archived_reason': None,
            'created_on': '2017-04-18T13:25:30.986208Z',
            'modified_on': '2017-04-18T13:25:30.986208Z',
        }

    def test_get_contact_without_view_document_permission(self):
        """Tests the contact detail view without view document permission."""
        contact = ContactFactory(
            archived_documents_url_path='http://some-documents',
        )
        user = create_test_user(
            permission_codenames=(
                'view_contact',
            ),
        )
        api_client = self.create_api_client(user=user)

        url = reverse(f'{self.endpoint_namespace}:contact:detail', kwargs={'pk': contact.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert 'archived_documents_url_path' not in response.json()

    @pytest.mark.parametrize('accepts_marketing', (True, False))
    def test_accepts_dit_email_marketing_consent_service(
        self,
        accepts_marketing,
        requests_mock,
    ):
        """
        Tests accepts_dit_email_marketing field is populated from the consent service.
        """
        contact = ContactFactory()
        hawk_response = HawkMockJSONResponse(
            api_id=settings.COMPANY_MATCHING_HAWK_ID,
            api_key=settings.COMPANY_MATCHING_HAWK_KEY,
            response={
                'results': [{
                    'email': contact.email,
                    'consents': [
                        CONSENT_SERVICE_EMAIL_CONSENT_TYPE,
                    ] if accepts_marketing else [],
                }],
            },
        )
        requests_mock.get(
            f'{settings.CONSENT_SERVICE_BASE_URL}'
            f'{CONSENT_SERVICE_PERSON_PATH_LOOKUP}',
            status_code=200,
            text=hawk_response,
        )
        api_client = self.create_api_client()

        url = reverse(f'{self.endpoint_namespace}:contact:detail', kwargs={'pk': contact.id})
        response = api_client.get(url)

        assert requests_mock.call_count == 1
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['accepts_dit_email_marketing'] == accepts_marketing

    @pytest.mark.parametrize(
        'response_status',
        (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_405_METHOD_NOT_ALLOWED,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ),
    )
    def test_accepts_dit_email_marketing_consent_service_http_error(
        self,
        response_status,
        requests_mock,
    ):
        """Tests accepts_dit_email_marketing field return false if there is an error."""
        contact = ContactFactory()
        requests_mock.get(
            f'{settings.CONSENT_SERVICE_BASE_URL}'
            f'{CONSENT_SERVICE_PERSON_PATH_LOOKUP}',
            status_code=response_status,
        )
        api_client = self.create_api_client()

        url = reverse(f'{self.endpoint_namespace}:contact:detail', kwargs={'pk': contact.id})
        response = api_client.get(url)

        assert requests_mock.call_count == 1
        assert response.json()['accepts_dit_email_marketing'] is False

    @pytest.mark.parametrize(
        'exceptions',
        (
            ConnectionError,
            ConnectTimeout,
            ReadTimeout,
        ),
    )
    def test_accepts_dit_email_marketing_consent_service_error(
        self,
        exceptions,
        requests_mock,
    ):
        """Tests accepts_dit_email_marketing field return false if there is an error."""
        contact = ContactFactory()
        requests_mock.get(
            f'{settings.CONSENT_SERVICE_BASE_URL}'
            f'{CONSENT_SERVICE_PERSON_PATH_LOOKUP}',
            exc=exceptions,
        )
        api_client = self.create_api_client()

        url = reverse(f'{self.endpoint_namespace}:contact:detail', kwargs={'pk': contact.id})
        response = api_client.get(url)

        assert requests_mock.call_count == 1
        assert response.json()['accepts_dit_email_marketing'] is False


class TestViewContactV3(ViewContactBase):
    """Tests for v3 view contacts endpoint"""

    endpoint_namespace = 'api-v3'


class TestViewContactV4(ViewContactBase):
    """Tests for v4 view contacts endpoint"""

    endpoint_namespace = 'api-v4'


class ContactListBase(APITestMixin):
    """List/filter contacts test case."""

    endpoint_namespace = None

    def test_contact_list_no_permissions(self):
        """Should return 403"""
        user = create_test_user(dit_team=TeamFactory())
        api_client = self.create_api_client(user=user)
        url = reverse(f'{self.endpoint_namespace}:contact:list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_all(self):
        """Test getting all contacts"""
        ContactFactory.create_batch(5)

        url = reverse(f'{self.endpoint_namespace}:contact:list')
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 5

    @freeze_time('2017-04-18 13:25:30.986208')
    def test_all_details(self):
        """Test response matches the inputted details when getting all contacts."""
        company = CompanyFactory()
        contact = ContactFactory(
            title_id=constants.Title.admiral_of_the_fleet.value.id,
            first_name='Oratio',
            last_name='Nelson',
            job_title='Head of Sales',
            company=company,
            email='foo@bar.com',
            primary=True,
            adviser=self.user,
            full_telephone_number='+44 123456789',
            address_same_as_company=False,
            address_1='Foo st.',
            address_2='adr 2',
            address_town='London',
            address_county='London',
            address_country_id=constants.Country.united_kingdom.value.id,
            address_postcode='SW1A1AA',
            notes='lorem ipsum',
        )

        url = reverse(f'{self.endpoint_namespace}:contact:list')
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'count': 1,
            'next': None,
            'previous': None,
            'results': [
                {
                    'address_1': 'Foo st.',
                    'address_2': 'adr 2',
                    'address_area': None,
                    'address_country': {
                        'id': constants.Country.united_kingdom.value.id,
                        'name': constants.Country.united_kingdom.value.name,
                    },
                    'address_county': 'London',
                    'address_postcode': 'SW1A1AA',
                    'address_same_as_company': False,
                    'address_town': 'London',
                    'adviser': {
                        'id': str(self.user.pk),
                        'first_name': self.user.first_name,
                        'last_name': self.user.last_name,
                        'name': self.user.name,
                    },
                    'archived': False,
                    'archived_by': None,
                    'archived_documents_url_path': contact.archived_documents_url_path,
                    'archived_on': None,
                    'archived_reason': None,
                    'company': {
                        'id': str(company.pk),
                        'name': company.name,
                    },
                    'created_on': '2017-04-18T13:25:30.986208Z',
                    'email': 'foo@bar.com',
                    'first_name': 'Oratio',
                    'job_title': 'Head of Sales',
                    'last_name': 'Nelson',
                    'modified_on': '2017-04-18T13:25:30.986208Z',
                    'name': 'Oratio Nelson',
                    'notes': 'lorem ipsum',
                    'primary': True,
                    'full_telephone_number': '+44 123456789',
                    'id': str(contact.pk),
                    'title': {
                        'id': constants.Title.admiral_of_the_fleet.value.id,
                        'name': constants.Title.admiral_of_the_fleet.value.name,
                    },
                },
            ],
        }

    def test_all_without_view_document_permission(self):
        """Test getting all contacts without view document permission."""
        ContactFactory.create_batch(5, archived_documents_url_path='https://some-docs')

        user = create_test_user(
            permission_codenames=(
                'view_contact',
            ),
        )
        api_client = self.create_api_client(user=user)

        url = reverse(f'{self.endpoint_namespace}:contact:list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 5
        assert all(
            'archived_documents_url_path' not in contact
            for contact in response.data['results']
        )

    def test_all_with_view_document_permission(self):
        """Test getting all contacts with view document permission."""
        ContactFactory.create_batch(5, archived_documents_url_path='https://some-docs')

        user = create_test_user(
            permission_codenames=(
                'view_contact',
                'view_contact_document',
            ),
        )
        api_client = self.create_api_client(user=user)

        url = reverse(f'{self.endpoint_namespace}:contact:list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 5
        assert all(
            contact['archived_documents_url_path'] == 'https://some-docs'
            for contact in response.data['results']
        )

    def test_contacts_are_sorted_by_created_on_desc(self):
        """Test contacts are sorted by created on desc."""
        datetimes = [date(year, 1, 1) for year in range(2015, 2030)]
        contacts = []

        for creation_datetime in datetimes:
            with freeze_time(creation_datetime):
                contacts.append(
                    ContactFactory(),
                )

        url = reverse(f'{self.endpoint_namespace}:contact:list')
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

        url = reverse(f'{self.endpoint_namespace}:contact:list')
        response = self.api_client.get(url, data={'company_id': company2.id})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        expected_contacts = {str(contact.id) for contact in contacts}
        assert {contact['id'] for contact in response.data['results']} == expected_contacts

    @pytest.mark.parametrize(
        'contacts,filter_,expected',
        (
            (
                ('aaa@aaa.aaa', 'bbb@bbb.bbb', 'ccc@ccc.ccc'),
                'bbb@bbb.bbb',
                {'bbb@bbb.bbb'},
            ),
            (
                ('aaa@aaa.aaa', 'bbb@bbb.bbb', 'aaa@aaa.aaa'),
                'aaa@aaa.aaa',
                {'aaa@aaa.aaa', 'aaa@aaa.aaa'},
            ),
            (
                ('aaa@aaa.aaa', 'bbb@bbb.bbb', 'aaa@aaa.aaa'),
                'xxx@xxx.xxx',
                set(),
            ),
        ),
    )
    def test_filter_by_email(self, contacts, filter_, expected):
        """Test getting contacts by email"""
        ContactFactory.create_batch(len(contacts), email=factory.Iterator(contacts))

        response = self.api_client.get(
            reverse(f'{self.endpoint_namespace}:contact:list'),
            data=dict(email=filter_),
        )

        assert response.status_code == status.HTTP_200_OK
        assert {res['email'] for res in response.data['results']} == expected


class TestContactListV3(ContactListBase):
    """Tests for v3 list contacts endpoint"""

    endpoint_namespace = 'api-v3'


class TestContactListV4(ContactListBase):
    """Tests for v4 list contacts endpoint"""

    endpoint_namespace = 'api-v4'


class ContactVersioningBase(APITestMixin):
    """
    Tests for versions created when interacting with the contact endpoints.
    """

    endpoint_namespace = None

    def test_add_creates_a_new_version(self):
        """Test that creating a contact creates a new version."""
        assert Version.objects.count() == 0

        response = self.api_client.post(
            reverse(f'{self.endpoint_namespace}:contact:list'),
            data={
                'first_name': 'Oratio',
                'last_name': 'Nelson',
                'company': {'id': CompanyFactory().pk},
                'email': 'foo@bar.com',
                'address_same_as_company': True,
                'primary': True,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['first_name'] == 'Oratio'
        assert response.data['last_name'] == 'Nelson'

        contact = Contact.objects.get(pk=response.data['id'])

        # check version created
        assert Version.objects.get_for_object(contact).count() == 1
        version = Version.objects.get_for_object(contact).first()
        assert version.revision.user == self.user
        assert version.field_dict['first_name'] == 'Oratio'
        assert version.field_dict['last_name'] == 'Nelson'
        assert not any(set(version.field_dict) & set(EXCLUDED_BASE_MODEL_FIELDS))

    def test_add_400_doesnt_create_a_new_version(self):
        """Test that if the endpoint returns 400, no version is created."""
        assert Version.objects.count() == 0

        response = self.api_client.post(
            reverse(f'{self.endpoint_namespace}:contact:list'),
            data={
                'first_name': 'Oratio',
                'last_name': 'Nelson',
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Version.objects.count() == 0

    def test_update_creates_a_new_version(self):
        """Test that updating a contact creates a new version."""
        contact = ContactFactory(
            first_name='Oratio',
            last_name='Nelson',
        )

        response = self.api_client.patch(
            reverse(f'{self.endpoint_namespace}:contact:detail', kwargs={'pk': contact.pk}),
            data={'first_name': 'New Oratio'},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['first_name'] == 'New Oratio'

        # check version created
        assert Version.objects.get_for_object(contact).count() == 1
        version = Version.objects.get_for_object(contact).first()
        assert version.revision.user == self.user
        assert version.field_dict['first_name'] == 'New Oratio'

    def test_update_400_doesnt_create_a_new_version(self):
        """Test that if the endpoint returns 400, no version is created."""
        contact = ContactFactory(
            first_name='Oratio',
            last_name='Nelson',
        )

        response = self.api_client.patch(
            reverse(f'{self.endpoint_namespace}:contact:detail', kwargs={'pk': contact.pk}),
            data={'email': 'invalid'},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Version.objects.get_for_object(contact).count() == 0


class TestContactV3Versioning(ContactVersioningBase):
    """Tests the V3 contacts versioning endpoint"""

    endpoint_namespace = 'api-v3'

    def test_archive_creates_a_new_version(self):
        """Test that archiving a contact creates a new version."""
        contact = ContactFactory()
        assert Version.objects.get_for_object(contact).count() == 0

        url = reverse('api-v3:contact:archive', kwargs={'pk': contact.id})
        response = self.api_client.post(url, data={'reason': 'foo'})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['archived']
        assert response.data['archived_reason'] == 'foo'

        # check version created
        assert Version.objects.get_for_object(contact).count() == 1
        version = Version.objects.get_for_object(contact).first()
        assert version.revision.user == self.user
        assert version.field_dict['archived']
        assert version.field_dict['archived_reason'] == 'foo'

    def test_archive_400_doesnt_create_a_new_version(self):
        """Test that if the endpoint returns 400, no version is created."""
        contact = ContactFactory()
        assert Version.objects.get_for_object(contact).count() == 0

        url = reverse('api-v3:contact:archive', kwargs={'pk': contact.id})
        response = self.api_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Version.objects.get_for_object(contact).count() == 0

    def test_unarchive_creates_a_new_version(self):
        """Test that unarchiving a contact creates a new version."""
        contact = ContactFactory(
            archived=True, archived_on=now(), archived_reason='foo',
        )
        assert Version.objects.get_for_object(contact).count() == 0

        url = reverse('api-v3:contact:unarchive', kwargs={'pk': contact.id})
        response = self.api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert not response.data['archived']
        assert response.data['archived_reason'] == ''

        # check version created
        assert Version.objects.get_for_object(contact).count() == 1
        version = Version.objects.get_for_object(contact).first()
        assert version.revision.user == self.user
        assert not version.field_dict['archived']


class TestContactV4Versioning(ContactVersioningBase):
    """Tests the V4 contacts versioning endpoint"""

    endpoint_namespace = 'api-v4'


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
        assert not set(EXCLUDED_BASE_MODEL_FIELDS) & entry['changes'].keys()
