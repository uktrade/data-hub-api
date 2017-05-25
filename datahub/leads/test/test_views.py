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
        url = reverse('api-v3:business-leads:lead')
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 1
        assert response_data['results'][0]['id'] == str(lead_this_user.id)
