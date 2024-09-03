import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.test_utils import APITestMixin
from datahub.investment_lead.models import EYBLead
from datahub.investment_lead.test.factories import EYBLeadFactory


EYB_CREATE_URL = reverse('api-v4:investment-lead:eyb-create')


class TestEYBLeadCreateAPI(APITestMixin):
    """EYB Lead Create view test case."""

    @pytest.mark.parametrize('method', ('delete', 'patch', 'get', 'put'))
    def test_methods_not_allowed(self, data_flow_api_client, method):
        """Tests that requests using unsupported methods return status code 405."""
        response = data_flow_api_client.request(method, EYB_CREATE_URL)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_post_with_no_payload(self, data_flow_api_client):
        """Tests if an error is raised when no payload is sent."""
        response = data_flow_api_client.post(EYB_CREATE_URL, json_={})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_with_incomplete_payload(self, eyb_lead_data, data_flow_api_client):
        """Tests if an error is raised when an incomplete payload is sent."""
        incomplete_data = eyb_lead_data.copy()
        incomplete_data.pop('location', None)
        response = data_flow_api_client.post(
            EYB_CREATE_URL, json_=[incomplete_data],
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_with_invalid_values_in_payload(self, eyb_lead_data, data_flow_api_client):
        """Tests if an error is raised when a payload with invalid values is sent."""
        invalid_data = eyb_lead_data.copy()
        invalid_data['location'] = None
        response = data_flow_api_client.post(
            EYB_CREATE_URL, json_=[invalid_data],
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'location' in response.data['errors'][0]['errors'].keys()

    def test_post_success(self, eyb_lead_data, data_flow_api_client):
        """Tests successful POST creates an EYB lead."""
        current_count = EYBLead.objects.count()
        response = data_flow_api_client.post(
            EYB_CREATE_URL, json_=[eyb_lead_data],
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert EYBLead.objects.count() == current_count + 1

    def test_post_does_not_create_duplicates(self, eyb_lead_data, data_flow_api_client):
        """Tests successful POST does not create duplicate EYB leads."""
        eyb_lead = EYBLeadFactory(**eyb_lead_data)
        assert EYBLead.objects.count() == 1

        modified_eyb_lead_data = eyb_lead_data.copy()
        modified_eyb_lead_data['location'] = 'different_location'
        response = data_flow_api_client.post(
            EYB_CREATE_URL, json_=[modified_eyb_lead_data],
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert EYBLead.objects.count() == 1
        eyb_lead.refresh_from_db()
        assert eyb_lead.location == modified_eyb_lead_data['location']
