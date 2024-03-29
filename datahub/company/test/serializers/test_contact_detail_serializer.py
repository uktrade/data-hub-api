from unittest.mock import Mock

import pytest
from django.conf import settings
from freezegun import freeze_time

from datahub.company.consent import CONSENT_SERVICE_PERSON_PATH_LOOKUP
from datahub.company.constants import (
    CONSENT_SERVICE_EMAIL_CONSENT_TYPE,
)
from datahub.company.serializers import ContactDetailSerializer, ContactDetailV4Serializer
from datahub.company.test.factories import CompanyFactory, ContactFactory
from datahub.core import constants
from datahub.core.test_utils import (
    HawkMockJSONResponse,
)

# mark the whole module for db use
pytestmark = pytest.mark.django_db

FROZEN_TIME = '2020-03-13T14:21:24.367265+00:00'

request = Mock(headers={
    'x-b3-traceid': '123',
    'x-b3-spanid': '456',
})


@pytest.fixture
def update_contact_task_mock(monkeypatch):
    mock_schedule_update_contact_consent = Mock()
    monkeypatch.setattr(
        'datahub.company.serializers.schedule_update_contact_consent',
        mock_schedule_update_contact_consent,
    )
    yield mock_schedule_update_contact_consent


@freeze_time(FROZEN_TIME)
class ContactSerializerBase:
    """
    Tests for the Contact Serializer. Checking that update / create notify the
    consent service correctly.
    """

    serializer = None

    def _make_contact(self):
        contact = ContactFactory()
        return contact

    def test_serializer_update_call_task(self, update_contact_task_mock, synchronous_on_commit):
        """
        Ensure that consent service RQ task is called when serializer.update
        is called if accepts_dit_email_marketing is True.
        """
        contact = self._make_contact()
        serialized_contact = self.serializer(
            instance=contact,
            context={'request': request},
        )
        serialized_contact.update(serialized_contact.instance, {
            'email': 'bar@foo.com',
            'accepts_dit_email_marketing': True,
        })
        update_contact_task_mock.assert_called_once_with(
            'bar@foo.com',
            True,
            kwargs={
                'modified_at': FROZEN_TIME,
                'zipkin_headers': request.headers,
            },
        )

    def test_serializer_update_partial_call_task(
            self,
            update_contact_task_mock,
            synchronous_on_commit,
    ):
        """
        Ensure that consent service RQ task is called when serializer.update
        is called with partial data if accepts_dit_email_marketing is True.
        """
        contact = self._make_contact()
        serialized_contact = self.serializer(instance=contact, partial=True)
        serialized_contact.update(serialized_contact.instance, {
            'accepts_dit_email_marketing': True,
        })
        update_contact_task_mock.assert_called_once_with(
            serialized_contact.instance.email,
            True,
            kwargs={'modified_at': FROZEN_TIME, 'zipkin_headers': {}},
        )

    def test_serializer_update_partial_not_call_task(
            self,
            update_contact_task_mock,
            synchronous_on_commit,
    ):
        """
        Ensure that consent service RQ task is not called when serializer.update
        is called with partial data but `accepts_dit_email_marketing` is missing.
        """
        contact = self._make_contact()
        serialized_contact = self.serializer(instance=contact, partial=True)
        data = {
            'last_name': 'Nelson1',
        }
        serialized_contact.update(serialized_contact.instance, data)

        assert not update_contact_task_mock.called

    def test_serializer_create_calls_task(self, update_contact_task_mock, synchronous_on_commit):
        """
        Ensure that consent service RQ task is called when serializer.create
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
            'primary': True,
            'full_telephone_number': '+44123456789',
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
        serialized_contact = self.serializer(data=data, context={'request': request})
        serialized_contact.is_valid(raise_exception=True)
        serialized_contact.create(serialized_contact.validated_data)
        update_contact_task_mock.assert_called_once_with(
            data['email'],
            data['accepts_dit_email_marketing'],
            kwargs={
                'modified_at': FROZEN_TIME,
                'zipkin_headers': request.headers,
            },
        )

    @pytest.mark.parametrize('accepts_marketing', (True, False))
    def test_marketing_field_populated_by_consent_service(
        self,
        requests_mock,
        accepts_marketing,
    ):
        """
        Test accepts_dit_email_marketing field is populated by the consent service.
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
        requests_mock.get(
            f'{settings.CONSENT_SERVICE_BASE_URL}'
            f'{CONSENT_SERVICE_PERSON_PATH_LOOKUP}',
            status_code=200,
            text=hawk_response,
        )
        contact_serialized = self.serializer(instance=contact)
        assert contact_serialized.data['accepts_dit_email_marketing'] is accepts_marketing
        assert requests_mock.call_count == 1


@freeze_time(FROZEN_TIME)
class TestContactV3Serializer(ContactSerializerBase):
    """
    Tests for the Contact V3 Serializer. Checking that update / create notify the
    consent service correctly.
    """

    serializer = ContactDetailSerializer


@freeze_time(FROZEN_TIME)
class TestContactV4Serializer(ContactSerializerBase):
    """
    Tests for the Contact V4 Serializer. Checking that update / create notify the
    consent service correctly.
    """

    serializer = ContactDetailV4Serializer

    @pytest.mark.parametrize(
        'country_id, expected_response, is_valid, address_area',
        (
            (
                constants.Country.united_states.value.id,
                {
                    'address_area': ['This field is required.'],
                },
                False,
                None,
            ),
            (
                constants.Country.canada.value.id,
                {
                    'address_area': ['This field is required.'],
                },
                False,
                None,
            ),
            (
                constants.Country.canada.value.id,
                {},
                True,
                {
                    'id': constants.AdministrativeArea.quebec.value.id,
                    'name': constants.AdministrativeArea.quebec.value.name,
                },
            ),
            (
                constants.Country.united_kingdom.value.id,
                {},
                True,
                None,
            ),
        ),
    )
    def test_area_required_validation_on_respective_countries(
        self,
        country_id,
        expected_response,
        is_valid,
        address_area,
    ):
        """
        Ensure that area required validation is called for appropriate countries
        and excluded for others
        """
        company = CompanyFactory()
        data = {
            'title': {
                'id': constants.Title.admiral_of_the_fleet.value.id,
            },
            'first_name': 'Jane',
            'last_name': 'Doe',
            'company': {
                'id': str(company.pk),
            },
            'primary': True,
            'email': 'foo@bar.com',
            'full_telephone_number': '+44123456789',
            'address_same_as_company': False,
            'address_1': 'Foo st.',
            'address_town': 'Bar',
            'address_country': {
                'id': country_id,
            },
            'address_area': address_area,
        }
        contact_serializer = ContactDetailV4Serializer(data=data, context={'request': request})
        assert contact_serializer.is_valid(raise_exception=False) is is_valid
        assert len(contact_serializer.errors) == len(expected_response)
        assert contact_serializer.errors == expected_response
