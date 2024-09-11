import pytest

from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core import constants
from datahub.core.test_utils import APITestMixin
from datahub.investment_lead.models import EYBLead
from datahub.investment_lead.test.factories import EYBLeadFactory
from datahub.investment_lead.test.utils import verify_eyb_lead_data


EYB_CREATE_URL = reverse('api-v4:investment-lead:eyb-create')

pytestmark = pytest.mark.django_db


class TestEYBLeadCreateAPI(APITestMixin):
    """Test for create/update EYB lead view (via POST request)"""

    @pytest.mark.parametrize('method', ('delete', 'patch', 'get', 'put'))
    def test_methods_not_allowed(self, data_flow_api_client, method):
        """Tests that requests using unsupported methods return status code 405."""
        response = data_flow_api_client.request(method, EYB_CREATE_URL)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_create_eyb_lead_list(self, data_flow_api_client, eyb_lead_post_data):
        """Tests that a list of leads are processed in a single request/response cycle."""
        response = data_flow_api_client.post(EYB_CREATE_URL, json_=[eyb_lead_post_data])
        assert response.status_code == status.HTTP_201_CREATED
        assert 'created' in response.data

        created_lead = response.data['created'][0]
        assert EYBLead.objects.count() == 1
        instance = EYBLead.objects.get(
            triage_hashed_uuid=created_lead['triage_hashed_uuid'],
            user_hashed_uuid=created_lead['user_hashed_uuid'],
        )
        verify_eyb_lead_data(instance, eyb_lead_post_data)

    def test_create_empty_list(self, data_flow_api_client):
        """Tests that no leads are created if an empty list is POSTed."""
        response = data_flow_api_client.post(EYB_CREATE_URL, json_=[])
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['error'] == 'Expected a list of leads.'

    def test_create_invalid_list(self, data_flow_api_client, eyb_lead_post_data):
        """Tests that no leads are created if a list containing invalid data is POSTed."""
        invalid_post_data = eyb_lead_post_data.copy()
        invalid_post_data['sector'] = None
        response = data_flow_api_client.post(EYB_CREATE_URL, json_=[invalid_post_data])
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'errors' in response.data

    def test_updating_existing_lead(self, data_flow_api_client, eyb_lead_post_data):
        """Tests that an existing lead is updated and does not create a duplicate."""
        existing_lead = EYBLeadFactory(
            triage_hashed_uuid=eyb_lead_post_data['triage_hashed_uuid'],
            user_hashed_uuid=eyb_lead_post_data['user_hashed_uuid'],
            location_id=constants.UKRegion.wales.value.id,
        )
        assert EYBLead.objects.count() == 1
        assert existing_lead.location.name == constants.UKRegion.wales.value.name

        modified_post_data = eyb_lead_post_data.copy()
        modified_post_data['location'] = constants.UKRegion.south_west.value.name
        response = data_flow_api_client.post(EYB_CREATE_URL, json_=[modified_post_data])
        assert response.status_code == status.HTTP_201_CREATED
        assert 'updated' in response.data

        updated_lead = response.data['updated'][0]
        assert EYBLead.objects.count() == 1
        instance = EYBLead.objects.get(
            triage_hashed_uuid=updated_lead['triage_hashed_uuid'],
            user_hashed_uuid=updated_lead['user_hashed_uuid'],
        )
        assert instance.triage_hashed_uuid == eyb_lead_post_data['triage_hashed_uuid']
        assert instance.user_hashed_uuid == eyb_lead_post_data['user_hashed_uuid']
        assert instance.location.name == constants.UKRegion.south_west.value.name
