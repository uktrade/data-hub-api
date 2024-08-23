from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.test_utils import APITestMixin
from datahub.investment_lead.models import EYBLead


class TestEYBLeadCreateAPI(APITestMixin):
    """
    EYB Lead Create view test case.
    """

    def test_get_not_allowed(self, eyb_lead_data):
        """
        Should return 405
        """
        post_url = reverse('api-v4:investment-lead:create')
        response = self.api_client.get(post_url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_post_with_no_payload(self):
        """
        Test that we get an Exception when no payload is sent
        """
        post_url = reverse('api-v4:investment-lead:create')
        response = self.api_client.post(post_url, data={})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_with_incomplete_payload(self, eyb_lead_data):
        """
        Test that we get an Exception when incomplete payload is sent
        """
        incomplete_data = eyb_lead_data.copy()
        incomplete_data['location'] = None

        post_url = reverse('api-v4:investment-lead:create')
        response = self.api_client.post(
            post_url, data=incomplete_data,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_success(self, eyb_lead_data):
        """
        Test successful POST to EYB
        """
        assert EYBLead.objects.count() == 0

        post_url = reverse('api-v4:investment-lead:create')
        response = self.api_client.post(
            post_url, data=eyb_lead_data,
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert EYBLead.objects.count() == 1
