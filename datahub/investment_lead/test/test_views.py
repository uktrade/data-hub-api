import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.test_utils import APITestMixin
from datahub.investment_lead.models import EYBLead


class TestEYBLeadCreateAPI(APITestMixin):
    """
    EYB Lead Create view test case.
    """

    @pytest.mark.parametrize('method', ('delete', 'patch', 'get', 'put'))
    def test_methods_not_allowed(self, eyb_lead_data, data_flow_api_client, method):
        """
        Should return 405
        """
        post_url = reverse('api-v4:investment-lead:create')
        response = data_flow_api_client.request(method, post_url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_post_with_no_payload(self, data_flow_api_client):
        """
        Test that we get an Exception when no payload is sent
        """
        post_url = reverse('api-v4:investment-lead:create')
        response = data_flow_api_client.post(post_url, json_={})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_with_incomplete_payload(self, eyb_lead_data, data_flow_api_client):
        """
        Test that we get an Exception when incomplete payload is sent
        """
        incomplete_data = eyb_lead_data.copy()
        incomplete_data['location'] = None

        post_url = reverse('api-v4:investment-lead:create')
        response = data_flow_api_client.post(
            post_url, json_=incomplete_data,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['location'][0] == 'This field may not be null.'

    def test_post_success(self, eyb_lead_data, data_flow_api_client):
        """
        Test successful POST to EYB
        """
        current_count = EYBLead.objects.count()

        post_url = reverse('api-v4:investment-lead:create')
        response = data_flow_api_client.post(
            post_url, json_=eyb_lead_data,
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert EYBLead.objects.count() == current_count + 1

    def test_post_does_not_create_duplicates(self, eyb_lead_data, data_flow_api_client):
        """
        Test successful POST to EYB does not create duplicates
        """
        current_count = EYBLead.objects.count()
        current_data = eyb_lead_data.copy()
        post_url = reverse('api-v4:investment-lead:create')

        # Create the first object
        response = data_flow_api_client.post(
            post_url, json_=current_data,
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert EYBLead.objects.count() == current_count + 1

        current_obj = EYBLead.objects.first()
        assert current_obj.location == current_data['location']

        # Change the data, create the "second object"
        current_data['location'] = 'different_location'
        response = data_flow_api_client.post(
            post_url, json_=current_data,
        )

        # Assert that no new object has been created but the data
        # has succesfully been updated
        assert response.status_code == status.HTTP_200_OK
        assert EYBLead.objects.count() == current_count + 1

        current_obj = EYBLead.objects.first()
        assert current_obj.location == current_data['location']
