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
                'first_name': 'Testo',
                'id': str(lead.advisor.pk),
                'last_name': 'Useri'
            },
            'archived': False,
            'archived_by': None,
            'archived_on': None,
            'archived_reason': None,
            'company': {
                'id': str(lead.company.pk),
                'name': 'name1'
            },
            'company_name': 'company name 1',
            'contactable_by_dit': False,
            'contactable_by_dit_partners': False,
            'contactable_by_email': True,
            'contactable_by_phone': False,
            'email': 'foo@bar.com',
            'email_alternative': None,
            'first_name': 'name 1',
            'id': str(lead.pk),
            'job_title': None,
            'last_name': 'surname 1',
            'notes': None,
            'telephone_alternative': None,
            'telephone_number': '+44 123456789'
        }

    def test_get_other_user_lead_failure(self):
        """Tests that getting a lead belonging to another user fails."""
        lead = BusinessLeadFactory()  # this lead is attached to another user
        url = reverse('api-v3:business-leads:lead-item', kwargs={
            'pk': lead.pk
        })
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
