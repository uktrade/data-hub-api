from unittest.mock import Mock

import pytest
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.constants import GET_CONSENT_FROM_CONSENT_SERVICE
from datahub.company.test.factories import (
    ArchivedContactFactory,
    ContactFactory,
    ContactWithOwnAddressFactory,
)
from datahub.core.test_utils import (
    format_date_or_datetime,
    get_attr_or_none,
)
from datahub.dataset.core.test import BaseDatasetViewTest
from datahub.feature_flag.test.factories import FeatureFlagFactory


def get_expected_data_from_contact(contact):
    """Returns expected dictionary based on given contact"""
    return {
        'accepts_dit_email_marketing': contact.accepts_dit_email_marketing,
        'address_1': contact.address_1,
        'address_2': contact.address_2,
        'address_country__name': get_attr_or_none(contact, 'address_country.name'),
        'address_county': contact.address_county,
        'address_postcode': contact.address_postcode,
        'address_same_as_company': contact.address_same_as_company,
        'address_town': contact.address_town,
        'archived': contact.archived,
        'archived_on': format_date_or_datetime(contact.archived_on),
        'company_id': str(contact.company_id) if contact.company_id is not None else None,
        'created_on': format_date_or_datetime(contact.created_on),
        'email': contact.email,
        'email_alternative': contact.email_alternative,
        'id': str(contact.id),
        'job_title': contact.job_title,
        'modified_on': format_date_or_datetime(contact.modified_on),
        'name': contact.name,
        'notes': contact.notes,
        'primary': contact.primary,
        'telephone_alternative': contact.telephone_alternative,
        'telephone_number': contact.telephone_number,
    }


@pytest.fixture
def consent_get_many_mock(monkeypatch):
    """Mocks the consent.get_many function"""
    m = Mock()
    monkeypatch.setattr('datahub.company.consent.get_many', m)
    yield m


@pytest.mark.django_db
class TestContactsDatasetViewSet(BaseDatasetViewTest):
    """
    Tests for ContactsDatasetView
    """

    view_url = reverse('api-v4:dataset:contacts-dataset')
    factory = ContactFactory

    @pytest.mark.parametrize(
        'contact_factory', (
            ArchivedContactFactory,
            ContactFactory,
            ContactWithOwnAddressFactory,
        ))
    def test_success(self, data_flow_api_client, contact_factory):
        """Test that endpoint returns with expected data for a single order"""
        contact = contact_factory()
        response = data_flow_api_client.get(self.view_url)
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

        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']
        assert len(response_results) == 4
        expected_contact_list = sorted([contact_3, contact_4],
                                       key=lambda item: item.pk) + [contact_1, contact_2]
        for index, contact in enumerate(expected_contact_list):
            assert contact.email == response_results[index]['email']

    def test_makes_api_call_to_consent_service(
            self,
            data_flow_api_client,
            consent_get_many_mock,
    ):
        """
        Test that if consent feature flag is enabled then call is made to
        the consent service and values from that are in the response.
        """
        FeatureFlagFactory(code=GET_CONSENT_FROM_CONSENT_SERVICE, is_active=True)
        contact1 = ContactFactory(email='a@a.a')
        contact2 = ContactFactory(email='b@b.b')
        contact3 = ContactFactory(email='c@c.c')
        consent_get_many_mock.return_value = {
            contact1.email: True,
            contact2.email: False,
        }
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
        consent_get_many_mock.assert_called_once_with(
            [contact1.email, contact2.email, contact3.email],
        )
        response_results = response.json()['results']
        assert response_results[0]['accepts_dit_email_marketing']
        assert not response_results[1]['accepts_dit_email_marketing']
        assert not response_results[2]['accepts_dit_email_marketing']
