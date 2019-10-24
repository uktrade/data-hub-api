import pytest
from django.conf import settings
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.test_utils import HawkAPITestClient
from datahub.metadata.models import Team
from datahub.metadata.test.factories import TeamFactory


@pytest.fixture
def hawk_api_client():
    """Hawk API client fixture."""
    yield HawkAPITestClient()


@pytest.fixture
def data_flow_api_client(hawk_api_client):
    """Hawk API client fixture configured to use credentials with the data_flow_api scope."""
    hawk_api_client.set_credentials(
        'data-flow-api-id',
        'data-flow-api-key',
    )
    yield hawk_api_client


def get_expected_data_from_team(team):
    """Returns team data as a dictionary"""
    return {
        'id': str(team.id),
        'name': team.name,
        'role__name': team.role.name,
        'uk_region__name': team.uk_region.name,
        'country__name': team.country.name,
    }


@pytest.mark.django_db
class TestTeamDatasetViewSet:
    """
    Tests for the teams data-flow export endpoint
    """

    view_url = reverse('api-v4:dataset:teams-dataset')

    @pytest.mark.parametrize('method', ('delete', 'patch', 'post', 'put'))
    def test_other_methods_not_allowed(
        self,
        data_flow_api_client,
        method,
    ):
        """Test that various HTTP methods are not allowed."""
        response = data_flow_api_client.request(method, self.view_url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_without_scope(self, hawk_api_client):
        """Test that making a request without the correct Hawk scope returns an error."""
        hawk_api_client.set_credentials(
            'test-id-without-scope',
            'test-key-without-scope',
        )
        response = hawk_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_without_credentials(self, api_client):
        """Test that making a request without credentials returns an error."""
        response = api_client.get(self.view_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_without_whitelisted_ip(self, data_flow_api_client):
        """Test that making a request without the whitelisted IP returns an error."""
        data_flow_api_client.set_http_x_forwarded_for('1.1.1.1')
        response = data_flow_api_client.get(self.view_url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_success(self, data_flow_api_client):
        """Test that endpoint returns with expected data for a single company"""
        response = data_flow_api_client.get(self.view_url)

        assert response.status_code == status.HTTP_200_OK

        response_team = response.json()['results'][0]
        team = Team.objects.get(id=response_team['id'])

        assert response_team == get_expected_data_from_team(team)

    def test_results_are_sorted(self, data_flow_api_client):
        """Test that endpoint returns correct order of records"""
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK

        results = response.json()['results']

        assert results == sorted(results, key=lambda t: t['id'])

    def test_pagination(self, data_flow_api_client):
        """Test that when page size higher than threshold response returns with next page url"""
        TeamFactory.create_batch(settings.REST_FRAMEWORK['PAGE_SIZE'] + 1)
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['next'] is not None

    def test_no_data(self, data_flow_api_client):
        """Test that without any data available, endpoint completes the request successfully"""
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
