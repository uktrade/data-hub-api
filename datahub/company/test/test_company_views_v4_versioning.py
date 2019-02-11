import reversion
from django.utils.timezone import now
from rest_framework import status
from rest_framework.reverse import reverse
from reversion.models import Version

from datahub.company.constants import BusinessTypeConstant
from datahub.company.models import Company
from datahub.company.test.factories import CompaniesHouseCompanyFactory, CompanyFactory
from datahub.core.constants import Country, UKRegion
from datahub.core.reversion import EXCLUDED_BASE_MODEL_FIELDS
from datahub.core.test_utils import (
    APITestMixin,
    format_date_or_datetime,
    random_obj_for_model,
)
from datahub.metadata.models import Sector


class TestCompanyVersioning(APITestMixin):
    """
    Tests for versions created when interacting with the company endpoints.
    """

    def test_add_creates_a_new_version(self):
        """Test that creating a company creates a new version."""
        assert Version.objects.count() == 0

        response = self.api_client.post(
            reverse('api-v4:company:collection'),
            data={
                'name': 'Acme',
                'trading_name': 'Trading name',
                'business_type': {'id': BusinessTypeConstant.company.value.id},
                'sector': {'id': random_obj_for_model(Sector).id},
                'address': {
                    'line_1': '75 Stramford Road',
                    'town': 'London',
                    'country': {
                        'id': Country.united_kingdom.value.id,
                    },
                },
                'uk_region': {'id': UKRegion.england.value.id},
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data['name'] == 'Acme'
        assert response_data['trading_name'] == 'Trading name'

        company = Company.objects.get(pk=response_data['id'])

        # check version created
        assert Version.objects.get_for_object(company).count() == 1
        version = Version.objects.get_for_object(company).first()
        assert version.revision.user == self.user
        assert version.field_dict['name'] == 'Acme'
        assert version.field_dict['trading_names'] == ['Trading name']
        assert not any(set(version.field_dict) & set(EXCLUDED_BASE_MODEL_FIELDS))

    def test_promoting_a_ch_company_creates_a_new_version(self):
        """Test that promoting a CH company to full company creates a new version."""
        assert Version.objects.count() == 0
        CompaniesHouseCompanyFactory(company_number=1234567890)

        response = self.api_client.post(
            reverse('api-v4:company:collection'),
            data={
                'name': 'Acme',
                'company_number': 1234567890,
                'business_type': BusinessTypeConstant.company.value.id,
                'sector': random_obj_for_model(Sector).id,
                'address': {
                    'line_1': '75 Stramford Road',
                    'town': 'London',
                    'country': {
                        'id': Country.united_kingdom.value.id,
                    },
                },
                'uk_region': UKRegion.england.value.id,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED

        company = Company.objects.get(pk=response.json()['id'])

        # check version created
        assert Version.objects.get_for_object(company).count() == 1
        version = Version.objects.get_for_object(company).first()
        assert version.field_dict['company_number'] == '1234567890'

    def test_add_400_doesnt_create_a_new_version(self):
        """Test that if the endpoint returns 400, no version is created."""
        assert Version.objects.count() == 0

        response = self.api_client.post(
            reverse('api-v4:company:collection'),
            data={'name': 'Acme'},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Version.objects.count() == 0

    def test_update_creates_a_new_version(self):
        """Test that updating a company creates a new version."""
        company = CompanyFactory(name='Foo ltd.')

        assert Version.objects.get_for_object(company).count() == 0

        response = self.api_client.patch(
            reverse('api-v4:company:item', kwargs={'pk': company.pk}),
            data={'name': 'Acme'},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['name'] == 'Acme'

        # check version created
        assert Version.objects.get_for_object(company).count() == 1
        version = Version.objects.get_for_object(company).first()
        assert version.revision.user == self.user
        assert version.field_dict['name'] == 'Acme'

    def test_update_400_doesnt_create_a_new_version(self):
        """Test that if the endpoint returns 400, no version is created."""
        company = CompanyFactory()

        response = self.api_client.patch(
            reverse('api-v4:company:item', kwargs={'pk': company.pk}),
            data={'trading_name': 'a' * 600},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Version.objects.get_for_object(company).count() == 0

    def test_archive_creates_a_new_version(self):
        """Test that archiving a company creates a new version."""
        company = CompanyFactory()
        assert Version.objects.get_for_object(company).count() == 0

        url = reverse('api-v4:company:archive', kwargs={'pk': company.id})
        response = self.api_client.post(url, data={'reason': 'foo'})

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['archived']
        assert response_data['archived_reason'] == 'foo'

        # check version created
        assert Version.objects.get_for_object(company).count() == 1
        version = Version.objects.get_for_object(company).first()
        assert version.revision.user == self.user
        assert version.field_dict['archived']
        assert version.field_dict['archived_reason'] == 'foo'

    def test_archive_400_doesnt_create_a_new_version(self):
        """Test that if the endpoint returns 400, no version is created."""
        company = CompanyFactory()
        assert Version.objects.get_for_object(company).count() == 0

        url = reverse('api-v4:company:archive', kwargs={'pk': company.id})
        response = self.api_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Version.objects.get_for_object(company).count() == 0

    def test_unarchive_creates_a_new_version(self):
        """Test that unarchiving a company creates a new version."""
        company = CompanyFactory(
            archived=True, archived_on=now(), archived_reason='foo',
        )
        assert Version.objects.get_for_object(company).count() == 0

        url = reverse('api-v4:company:unarchive', kwargs={'pk': company.id})
        response = self.api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert not response_data['archived']
        assert response_data['archived_reason'] == ''

        # check version created
        assert Version.objects.get_for_object(company).count() == 1
        version = Version.objects.get_for_object(company).first()
        assert version.revision.user == self.user
        assert not version.field_dict['archived']


class TestAuditLogView(APITestMixin):
    """Tests for the audit log view."""

    def test_audit_log_view(self):
        """Test retrieval of audit log."""
        initial_datetime = now()
        with reversion.create_revision():
            company = CompanyFactory(
                description='Initial desc',
            )

            reversion.set_comment('Initial')
            reversion.set_date_created(initial_datetime)
            reversion.set_user(self.user)

        changed_datetime = now()
        with reversion.create_revision():
            company.description = 'New desc'
            company.save()

            reversion.set_comment('Changed')
            reversion.set_date_created(changed_datetime)
            reversion.set_user(self.user)

        versions = Version.objects.get_for_object(company)
        version_id = versions[0].id
        url = reverse('api-v4:company:audit-item', kwargs={'pk': company.pk})

        response = self.api_client.get(url)
        response_data = response.json()['results']

        # No need to test the whole response
        assert len(response_data) == 1
        entry = response_data[0]

        assert entry['id'] == version_id
        assert entry['user']['name'] == self.user.name
        assert entry['comment'] == 'Changed'
        assert entry['timestamp'] == format_date_or_datetime(changed_datetime)
        assert entry['changes']['description'] == ['Initial desc', 'New desc']
        assert not set(EXCLUDED_BASE_MODEL_FIELDS) & entry['changes'].keys()
