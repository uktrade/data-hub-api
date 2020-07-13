from unittest.mock import Mock

import pytest
from django.conf import settings
from freezegun import freeze_time

from datahub.company.consent import CONSENT_SERVICE_PERSON_PATH_LOOKUP
from datahub.company.constants import (
    CONSENT_SERVICE_EMAIL_CONSENT_TYPE,
    GET_CONSENT_FROM_CONSENT_SERVICE,
)
from datahub.company.serializers import ContactDetailSerializer
from datahub.company.test.factories import CompanyFactory, ContactFactory
from datahub.core import constants
from datahub.core.test_utils import (
    HawkMockJSONResponse,
)
from datahub.feature_flag.test.factories import FeatureFlagFactory

# mark the whole module for db use
pytestmark = pytest.mark.django_db

FROZEN_TIME = '2020-03-13T14:21:24.367265+00:00'


@pytest.fixture
def update_contact_task_mock(monkeypatch):
    """Mocks the apply_async method of the update_contact_consent celery task"""
    m = Mock()
    monkeypatch.setattr('datahub.company.serializers.update_contact_consent.apply_async', m)
    yield m


@pytest.fixture
def get_consent_from_api_feature_flag():
    """
    Creates the get consent from consent service feature flag.
    """
    yield FeatureFlagFactory(code=GET_CONSENT_FROM_CONSENT_SERVICE)


@freeze_time(FROZEN_TIME)
class TestContactSerializer:
    """
    Tests for the Contact Serializer. Checking that update / create notify the
    consent service correctly.
    """

    def _make_contact(self, accepts_dit_email_marketing=False):
        contact = ContactFactory(
            accepts_dit_email_marketing=accepts_dit_email_marketing,
        )
        return contact

    def test_serializer_update_call_task(self, update_contact_task_mock, synchronous_on_commit):
        """
        Ensure that consent service celery task is called when serializer.update
        is called.
        """
        contact = self._make_contact()
        c = ContactDetailSerializer(instance=contact)
        data = {
            'email': 'bar@foo.com',
            'accepts_dit_email_marketing': True,
        }
        c.update(c.instance, data)
        update_contact_task_mock.assert_called_once_with(
            args=(data['email'], data['accepts_dit_email_marketing']),
            kwargs={'modified_at': FROZEN_TIME},
        )

    def test_serializer_update_partial_call_task(
            self,
            update_contact_task_mock,
            synchronous_on_commit,
    ):
        """
        Ensure that consent service celery task is called when serializer.update
        is called with partial data.
        """
        contact = self._make_contact()
        c = ContactDetailSerializer(instance=contact, partial=True)
        data = {
            'accepts_dit_email_marketing': True,
        }
        c.update(c.instance, data)
        update_contact_task_mock.assert_called_once_with(
            args=(c.instance.email, data['accepts_dit_email_marketing']),
            kwargs={'modified_at': FROZEN_TIME},
        )

    def test_serializer_update_partial_not_call_task(
            self,
            update_contact_task_mock,
            synchronous_on_commit,
    ):
        """
        Ensure that consent service celery task not is called when serializer.update
        is called with partial data but `accepts_dit_email_marketing` is missing.
        """
        contact = self._make_contact()
        c = ContactDetailSerializer(instance=contact, partial=True)
        data = {
            'last_name': 'Nelson1',
        }
        c.update(c.instance, data)

        assert not update_contact_task_mock.called

    def test_serializer_create_calls_task(self, update_contact_task_mock, synchronous_on_commit):
        """
        Ensure that consent service celery task is called when serializer.create
        is called.
        """
        company = CompanyFactory()
        data = {
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
            },
            'address_postcode': 'SW1A1AA',
            'notes': 'lorem ipsum',
            'accepts_dit_email_marketing': True,
        }
        c = ContactDetailSerializer(data=data)
        c.is_valid(raise_exception=True)
        c.create(c.validated_data)
        update_contact_task_mock.assert_called_once_with(
            args=(data['email'], data['accepts_dit_email_marketing']),
            kwargs={'modified_at': FROZEN_TIME},
        )

    @pytest.mark.parametrize('accepts_marketing', (True, False))
    def test_to_representation_feature_flag_on(
        self,
        requests_mock,
        get_consent_from_api_feature_flag,
        accepts_marketing,
    ):
        """
        Test accepts_dit_email_marketing fields is populated by the consent service
        when the feature flag is enabled.
        """
        contact = self._make_contact()
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
        requests_mock.post(
            f'{settings.CONSENT_SERVICE_BASE_URL}'
            f'{CONSENT_SERVICE_PERSON_PATH_LOOKUP}',
            status_code=200,
            text=hawk_response,
        )
        contact_serialized = ContactDetailSerializer(instance=contact)
        assert contact_serialized.data['accepts_dit_email_marketing'] is accepts_marketing
        assert requests_mock.call_count == 1

    @pytest.mark.parametrize('accepts_marketing', (True, False))
    def test_to_representation_feature_flag_off(
        self,
        requests_mock,
        accepts_marketing,
    ):
        """
        Test accepts_dit_email_marketing fields is populated by the db
        and no calls are made to the consent service when the feature flag is disabled.
        """
        contact = self._make_contact(accepts_dit_email_marketing=accepts_marketing)
        requests_mock.post(
            f'{settings.CONSENT_SERVICE_BASE_URL}'
            f'{CONSENT_SERVICE_PERSON_PATH_LOOKUP}',
            status_code=200,
        )
        contact_serialized = ContactDetailSerializer(instance=contact)
        assert contact_serialized.data['accepts_dit_email_marketing'] is accepts_marketing
        assert requests_mock.called is False
