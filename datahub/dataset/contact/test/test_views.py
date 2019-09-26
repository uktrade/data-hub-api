import pytest
from django.conf import settings
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import (
    ArchivedContactFactory,
    ContactFactory,
    ContactWithOwnAddressFactory,
)
from datahub.core.test_utils import (
    format_date_or_datetime,
    get_attr_or_none,
    HawkAPITestClient,
)


@pytest.fixture
def hawk_api_client():
    """Hawk API client fixture."""
    yield HawkAPITestClient()


@pytest.fixture
def data_flow_api_client(hawk_api_client):
    """Hawk API client fixture configured to use credentials with the data_flow_api scope."""
    hawk_api_client.set_credentials(
        'data-flow-api-id',
        'data-flow-api-key',
    )
    yield hawk_api_client


def get_expected_data_from_contact(contact):
    """Returns expected dictionary based on given contact"""
    return {
        'accepts_dit_email_marketing': contact.accepts_dit_email_marketing,
        'address_country__name': get_attr_or_none(contact, 'address_country.name'),
        'address_postcode': contact.address_postcode,
        'company__company_number': get_attr_or_none(contact, 'company.company_number'),
        'company__name': get_attr_or_none(contact, 'company.name'),
        'company__uk_region__name': get_attr_or_none(contact, 'company.uk_region.name'),
        'company_sector': get_attr_or_none(contact, 'company.sector.name'),
        'created_on': format_date_or_datetime(contact.created_on),
        'email': contact.email,
        'email_alternative': contact.email_alternative,
        'id': str(contact.id),
        'job_title': contact.job_title,
        'name': contact.name,
        'notes': contact.notes,
        'telephone_alternative': contact.telephone_alternative,
        'telephone_number': contact.telephone_number,
    }


@pytest.mark.django_db
class TestContactsDatasetViewSet:
    """
    Tests for ContactsDatasetView
    """

    contacts_dataset_view_url = reverse('api-v4:dataset:contacts-dataset')

    @pytest.mark.parametrize('method', ('delete', 'patch', 'post', 'put'))
    def test_other_methods_not_allowed(
        self,
        data_flow_api_client,
        method,
    ):
        """Test that various HTTP methods are not allowed."""
        response = data_flow_api_client.request(method, self.contacts_dataset_view_url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_without_scope(self, hawk_api_client):
        """Test that making a request without the correct Hawk scope returns an error."""
        hawk_api_client.set_credentials(
            'test-id-without-scope',
            'test-key-without-scope',
        )
        response = hawk_api_client.get(self.contacts_dataset_view_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_without_credentials(self, api_client):
        """Test that making a request without credentials returns an error."""
        response = api_client.get(self.contacts_dataset_view_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize(
        'contact_factory', (
            ArchivedContactFactory,
            ContactFactory,
            ContactWithOwnAddressFactory,
        ))
    def test_success(self, data_flow_api_client, contact_factory):
        """Test that endpoint returns with expected data for a single order"""
        contact = contact_factory()
        response = data_flow_api_client.get(self.contacts_dataset_view_url)
        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']
        assert len(response_results) == 1
        result = response_results[0]
        expected_result = get_expected_data_from_contact(contact)
        assert result == expected_result

    def test_with_multiple_contacts(self, data_flow_api_client):
        """Test that endpoint returns correct number of record in expected contact"""
        with freeze_time('2019-01-01 12:30:00'):
            contact_1 = ContactFactory()
        with freeze_time('2019-01-03 12:00:00'):
            contact_2 = ContactFactory()
        with freeze_time('2019-01-01 12:00:00'):
            contact_3 = ContactFactory()
            contact_4 = ContactFactory()

        response = data_flow_api_client.get(self.contacts_dataset_view_url)
        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']
        assert len(response_results) == 4
        expected_contact_list = sorted(
            [contact_1, contact_2, contact_3, contact_4],
            key=lambda item: (item.id, item.created_on),
        )
        for index, contact in enumerate(expected_contact_list):
            assert contact.email == response_results[index]['email']

    def test_pagination(self, data_flow_api_client):
        """Test that when page size higher than threshold response returns with next page url"""
        ContactFactory.create_batch(settings.REST_FRAMEWORK['PAGE_SIZE'] + 1)
        response = data_flow_api_client.get(self.contacts_dataset_view_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['next'] is not None

    def test_no_data(self, data_flow_api_client):
        """Test that without any data available, endpoint completes the request successfully"""
        response = data_flow_api_client.get(self.contacts_dataset_view_url)
        assert response.status_code == status.HTTP_200_OK
