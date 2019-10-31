import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.dataset.core.test import BaseDatasetViewTest
from datahub.metadata.models import Team
from datahub.metadata.test.factories import TeamFactory


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
class TestTeamDatasetViewSet(BaseDatasetViewTest):
    """
    Tests for the teams data-flow export endpoint
    """

    view_url = reverse('api-v4:dataset:teams-dataset')
    factory = TeamFactory

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
