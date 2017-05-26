"""Tests for business lead views."""

from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.test_utils import LeelooTestCase
from datahub.leads.test.factories import BusinessLeadFactory


class BusinessLeadViewsTestCase(LeelooTestCase):
    """Business lead views test case."""

    def test_list_leads_success(self):
        """Tests listing leads.

        Ensures that only the user's leads are returned.
        """
        lead_this_user = BusinessLeadFactory(advisor=self.user)
        BusinessLeadFactory()  # this lead is attached to another user
        url = reverse('api-v3:business-leads:lead-collection')
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 1
        assert response_data['results'][0]['id'] == str(lead_this_user.id)

    def test_get_success(self):
        """Tests that getting a single lead."""
        lead = BusinessLeadFactory(advisor=self.user)  # this lead is attached
        #  to another user
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
            'advisor': {
                'first_name': self.user.first_name,
                'id': str(self.user.pk),
                'last_name': self.user.last_name
            },
            'archived': False,
            'archived_by': None,
            'archived_on': None,
            'archived_reason': None,
            'company': {
                'id': str(lead.company.pk),
                'name': str(lead.company.name)
            },
            'company_name': lead.company_name,
            'contactable_by_dit': False,
            'contactable_by_dit_partners': False,
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

    def test_get_other_user_lead_failure(self):
        """Tests that getting a lead belonging to another user fails."""
        lead = BusinessLeadFactory()  # this lead is attached to another user
        url = reverse('api-v3:business-leads:lead-item', kwargs={
            'pk': lead.pk
        })
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_lead_success(self):
        """Tests successfully creating a business lead."""
        url = reverse('api-v3:business-leads:lead-collection')
        request_data = {
            'first_name': 'First name',
            'last_name': 'Last name',
            'telephone_number': '+44 7000 123456'
        }
        response = self.api_client.post(url, format='json', data=request_data)

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data['first_name'] == request_data['first_name']
        assert response_data['last_name'] == request_data['last_name']
        assert (response_data['telephone_number'] == request_data[
            'telephone_number'])
        assert response_data['advisor']['id'] == str(self.user.pk)

    def test_create_lead_failure(self):
        """Tests creating a business lead without required fields."""
        url = reverse('api-v3:business-leads:lead-collection')
        request_data = {}
        response = self.api_client.post(url, format='json', data=request_data)

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
        lead = BusinessLeadFactory(advisor=self.user)
        url = reverse('api-v3:business-leads:lead-item', kwargs={
            'pk': lead.pk
        })
        request_data = {
            'first_name': 'New first name',
            'email_alternative': 'altemail@blah.com'
        }
        response = self.api_client.patch(url, format='json', data=request_data)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['first_name'] == request_data['first_name']
        assert (response_data['email_alternative'] == request_data[
            'email_alternative'])

    def test_patch_failure(self):
        """Tests updating a business lead."""
        lead = BusinessLeadFactory(advisor=self.user)
        url = reverse('api-v3:business-leads:lead-item', kwargs={
            'pk': lead.pk
        })
        request_data = {
            'first_name': None,
            'company_name': None,
            'company': None
        }
        response = self.api_client.patch(url, format='json', data=request_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'first_name': ['Company name or first name and last name '
                           'required'],
            'last_name': ['Company name or first name and last name required'],
            'company_name': ['Company name or first name and last name '
                             'required']
        }
