"""Tests for business lead views."""

from datetime import datetime

from django.utils.timezone import utc
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.test_utils import APITestMixin, create_test_user
from datahub.leads.test.factories import BusinessLeadFactory
from datahub.metadata.test.factories import TeamFactory

FROZEN_TIME = '2017-04-18T13:25:30.986208Z'


class TestBusinessLeadViews(APITestMixin):
    """Business lead views test case."""

    def test_no_permissions(self):
        """Should return 403"""
        user = create_test_user(dit_team=TeamFactory())
        api_client = self.create_api_client(user=user)
        url = reverse('api-v3:business-leads:lead-collection')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_leads_success(self):
        """Tests listing leads, filtered by creator.
        """
        lead_this_user = BusinessLeadFactory(created_by=self.user)
        BusinessLeadFactory()  # this lead is attached to another user
        url = reverse('api-v3:business-leads:lead-collection')
        response = self.api_client.get(url, {'created_by_id': str(self.user.id)})

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 1
        assert response_data['results'][0]['id'] == str(lead_this_user.id)

    def test_get_success(self):
        """Tests that getting a single lead."""
        lead = BusinessLeadFactory(created_by=self.user)
        url = reverse('api-v3:business-leads:lead-item', kwargs={
            'pk': lead.pk
        })
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data == {
            'address_1': None,
            'address_2': None,
            'address_country': None,
            'address_county': None,
            'address_postcode': None,
            'address_town': None,
            'created_by': {
                'first_name': self.user.first_name,
                'id': str(self.user.pk),
                'last_name': self.user.last_name,
                'name': self.user.name
            },
            'modified_by': {
                'first_name': lead.modified_by.first_name,
                'id': str(lead.modified_by.pk),
                'last_name': lead.modified_by.last_name,
                'name': lead.modified_by.name
            },
            'archived': False,
            'archived_by': None,
            'archived_on': None,
            'archived_reason': None,
            'company': {
                'id': str(lead.company.pk),
                'name': lead.company.name
            },
            'company_name': lead.company_name,
            'contactable_by_dit': False,
            'contactable_by_uk_dit_partners': False,
            'contactable_by_overseas_dit_partners': False,
            'accepts_dit_email_marketing': False,
            'contactable_by_email': True,
            'contactable_by_phone': False,
            'email': 'foo@bar.com',
            'email_alternative': None,
            'first_name': lead.first_name,
            'id': str(lead.pk),
            'job_title': None,
            'last_name': lead.last_name,
            'notes': None,
            'telephone_alternative': None,
            'telephone_number': '+44 123456789',
            'trading_name': None
        }

    def test_create_lead_success(self):
        """Tests successfully creating a business lead."""
        url = reverse('api-v3:business-leads:lead-collection')
        request_data = {
            'first_name': 'First name',
            'last_name': 'Last name',
            'telephone_number': '+44 7000 123456'
        }
        response = self.api_client.post(url, data=request_data)

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data['first_name'] == request_data['first_name']
        assert response_data['last_name'] == request_data['last_name']
        assert (response_data['telephone_number'] == request_data[
            'telephone_number'])
        assert response_data['created_by']['id'] == str(self.user.pk)

    def test_create_lead_failure(self):
        """Tests creating a business lead without required fields."""
        url = reverse('api-v3:business-leads:lead-collection')
        request_data = {}
        response = self.api_client.post(url, data=request_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'first_name': ['Company name or first name and last name '
                           'required'],
            'last_name': ['Company name or first name and last name required'],
            'company_name': ['Company name or first name and last name '
                             'required'],
            'email': ['Email address or phone number required'],
            'telephone_number': ['Email address or phone number required']
        }

    def test_patch_success(self):
        """Tests updating a business lead."""
        lead = BusinessLeadFactory(created_by=self.user)
        url = reverse('api-v3:business-leads:lead-item', kwargs={
            'pk': lead.pk
        })
        request_data = {
            'first_name': 'New first name',
            'email_alternative': 'altemail@blah.com'
        }
        response = self.api_client.patch(url, data=request_data)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['first_name'] == request_data['first_name']
        assert (response_data['email_alternative'] == request_data[
            'email_alternative'])

    def test_patch_failure(self):
        """Tests updating a business lead."""
        lead = BusinessLeadFactory(created_by=self.user)
        url = reverse('api-v3:business-leads:lead-item', kwargs={
            'pk': lead.pk
        })
        request_data = {
            'first_name': None,
            'company_name': None,
            'company': None
        }
        response = self.api_client.patch(url, data=request_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'first_name': ['Company name or first name and last name '
                           'required'],
            'last_name': ['Company name or first name and last name required'],
            'company_name': ['Company name or first name and last name '
                             'required']
        }

    @freeze_time(FROZEN_TIME)
    def test_archive_success(self):
        """Tests archiving a business lead."""
        lead = BusinessLeadFactory(created_by=self.user)
        url = reverse('api-v3:business-leads:archive-lead-item', kwargs={
            'pk': lead.pk
        })
        request_data = {
            'reason': 'archive test'
        }
        response = self.api_client.post(url, data=request_data)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['archived'] is True
        assert response_data['archived_by']['id'] == str(self.user.pk)
        assert response_data['archived_reason'] == 'archive test'
        assert response_data['archived_on'] == FROZEN_TIME

    def test_unarchive_success(self):
        """Tests unarchiving a business lead."""
        lead = BusinessLeadFactory(
            created_by=self.user, archived=True, archived_by=self.user,
            archived_reason='unarchive test', archived_on=datetime(2016, 1, 1, tzinfo=utc)
        )
        url = reverse('api-v3:business-leads:unarchive-lead-item', kwargs={
            'pk': lead.pk
        })
        response = self.api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['archived'] is False
        assert response_data['archived_by'] is None
        assert response_data['archived_reason'] == ''
        assert response_data['archived_on'] is None
