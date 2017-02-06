import json
import uuid
from unittest import mock

import pytest
from django.conf import settings
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from datahub.company.models import Contact
from datahub.core import constants
from datahub.core.test_utils import LeelooTestCase
from datahub.es.utils import document_exists, get_elasticsearch_client
from datahub.korben.utils import generate_signature
from .factories import CompanyFactory, ContactFactory

# mark the whole module for db use
pytestmark = pytest.mark.django_db


def _signature(url, data):
    """Return the signature to authenticate the api client for the tests in this module."""
    return generate_signature(url, data, settings.DATAHUB_SECRET)


class ContactTestCase(LeelooTestCase):
    """Contact test case."""

    @mock.patch('datahub.core.viewsets.tasks.save_to_korben')
    def test_add_contact_address_same_as_company(self, mocked_save_to_korben):
        """Test add new contact."""
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
            'primary': True
        })

        assert response.status_code == status.HTTP_201_CREATED
        # make sure we're spawning a task to save to Korben
        expected_data = Contact.objects.get(pk=response.data['id']).convert_model_to_korben_format()
        mocked_save_to_korben.delay.assert_called_once_with(
            db_table='company_contact',
            data=expected_data,
            update=False,
            user_id=self.user.id
        )
        # make sure we're writing to ES
        es_client = get_elasticsearch_client()
        assert document_exists(
            client=es_client,
            doc_type='company_contact',
            document_id=response.data['id']
        )

    @mock.patch('datahub.core.viewsets.tasks.save_to_korben')
    def test_add_contact_no_address(self, mocked_save_to_korben):
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

        assert mocked_save_to_korben.delay.called is False
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['errors'] == {
            'address_same_as_company': ['Please select either address_same_as_company or enter an address manually.']
        }

    @mock.patch('datahub.core.viewsets.tasks.save_to_korben')
    def test_add_contact_partial_manual_address(self, mocked_save_to_korben):
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

        assert mocked_save_to_korben.delay.called is False
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['errors'] == {
            'address_country': ['This field may not be null.'],
            'address_town': ['This field may not be null.']
        }

    @mock.patch('datahub.core.viewsets.tasks.save_to_korben')
    def test_add_contact_manual_address(self, mocked_save_to_korben):
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
            'primary': True
        })

        assert response.status_code == status.HTTP_201_CREATED
        # make sure we're spawning a task to save to Korben
        expected_data = Contact.objects.get(pk=response.data['id']).convert_model_to_korben_format()
        mocked_save_to_korben.delay.assert_called_once_with(
            db_table='company_contact',
            data=expected_data,
            update=False,
            user_id=self.user.id
        )
        # make sure we're writing to ES
        es_client = get_elasticsearch_client()
        assert document_exists(
            client=es_client,
            doc_type='company_contact',
            document_id=response.data['id']
        )

    @mock.patch('datahub.core.viewsets.tasks.save_to_korben')
    @freeze_time('2017-01-27 12:00:01')
    def test_modify_contact(self, mocked_save_to_korben):
        """Modify an existing contact."""
        contact = ContactFactory(first_name='Foo')

        url = reverse('v1:contact-detail', kwargs={'pk': contact.pk})
        response = self.api_client.patch(url, {
            'first_name': 'bar',
        })

        assert response.status_code == status.HTTP_200_OK, response.data
        assert response.data['first_name'] == 'bar'
        # make sure we're spawning a task to save to Korben
        expected_data = contact.convert_model_to_korben_format()
        expected_data['first_name'] = 'bar'
        mocked_save_to_korben.delay.assert_called_once_with(
            db_table='company_contact',
            data=expected_data,
            update=True,  # this is an update!
            user_id=self.user.id
        )
        # make sure we're writing to ES
        es_client = get_elasticsearch_client()
        es_result = es_client.get(
            index=settings.ES_INDEX,
            doc_type='company_contact',
            id=response.data['id'],
            realtime=True
        )
        assert es_result['_source']['first_name'] == 'bar'

    def test_archive_contact_no_reason(self):
        """Test archive contact without providing a reason."""
        contact = ContactFactory()
        url = reverse('v1:contact-archive', kwargs={'pk': contact.pk})
        response = self.api_client.post(url)

        assert response.data['archived']
        assert response.data['archived_reason'] == ''
        assert response.data['id'] == contact.pk

        # make sure we're writing to ES
        es_client = get_elasticsearch_client()
        es_result = es_client.get(
            index=settings.ES_INDEX,
            doc_type='company_contact',
            id=response.data['id'],
            realtime=True
        )
        assert es_result['_source']['archived']
        assert es_result['_source']['archived_reason'] == ''

    def test_archive_contact_reason(self):
        """Test archive contact providing a reason."""
        contact = ContactFactory()
        url = reverse('v1:contact-archive', kwargs={'pk': contact.pk})
        response = self.api_client.post(url, {'reason': 'foo'})

        assert response.data['archived']
        assert response.data['archived_reason'] == 'foo'
        assert response.data['id'] == contact.pk

        # make sure we're writing to ES
        es_client = get_elasticsearch_client()
        es_result = es_client.get(
            index=settings.ES_INDEX,
            doc_type='company_contact',
            id=response.data['id'],
            realtime=True
        )
        assert es_result['_source']['archived']
        assert es_result['_source']['archived_reason'] == 'foo'

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

    def test_get_invalid_contact_coming_from_korben(self):
        """Do a GET with incomplete address coming from Korben."""
        # create the incomplete address contact using the Korben API first
        company = CompanyFactory()
        url = reverse('korben:company_contact')
        data_dict = {
            'id': str(uuid.uuid4()),
            'title_id': constants.Title.wing_commander.value.id,
            'first_name': 'Bat',
            'last_name': 'Man',
            'job_title': constants.Role.owner.value.name,
            'company_id': company.id,
            'email': 'foo@bar.com',
            'telephone_countrycode': '+44',
            'telephone_number': '123456789',
            'address_1': '14 Hello street',
            'primary': True
        }
        data = json.dumps(data_dict)
        api_client = APIClient()
        api_client.credentials(**{'HTTP_X_SIGNATURE': _signature(url, data)})
        response = api_client.post(url, data, content_type='application/json')

        assert response.status_code == status.HTTP_200_OK

        # now do a GET
        url = reverse('v1:contact-detail', kwargs={'pk': data_dict['id']})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == data_dict['id']
