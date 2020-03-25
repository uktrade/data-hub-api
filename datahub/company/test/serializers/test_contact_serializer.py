from unittest.mock import Mock

import pytest
from freezegun import freeze_time

from datahub.company.serializers import ContactSerializer
from datahub.company.test.factories import CompanyFactory, ContactFactory
from datahub.core import constants

# mark the whole module for db use
pytestmark = pytest.mark.django_db

FROZEN_TIME = '2020-03-13T14:21:24.367265+00:00'


@pytest.fixture
def update_contact_task_mock(monkeypatch):
    """Mocks the apply_async method of the update_contact_consent celery task"""
    m = Mock()
    monkeypatch.setattr('datahub.company.serializers.update_contact_consent.apply_async', m)
    yield m


@freeze_time(FROZEN_TIME)
class TestContactSerializer:
    """
    Tests for the Contact Serializer. Checking that update / create notify the
    consent service correctly.
    """

    def _make_contact(self):
        contact = ContactFactory(
            accepts_dit_email_marketing=False,
        )
        return contact

    def test_serializer_update_call_task(self, update_contact_task_mock, synchronous_on_commit):
        """
        Ensure that consent service celery task is called when serializer.update
        is called.
        """
        contact = self._make_contact()
        c = ContactSerializer(instance=contact)
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
        c = ContactSerializer(instance=contact, partial=True)
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
        c = ContactSerializer(instance=contact, partial=True)
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
        c = ContactSerializer(data=data)
        c.is_valid(raise_exception=True)
        c.create(c.validated_data)
        update_contact_task_mock.assert_called_once_with(
            args=(data['email'], data['accepts_dit_email_marketing']),
            kwargs={'modified_at': FROZEN_TIME},
        )
