from datetime import datetime

import pytest

from django.utils.timezone import utc
from freezegun import freeze_time
from rest_framework import status

from rest_framework.reverse import reverse

from datahub.core.test_utils import format_date_or_datetime
from datahub.dataset.core.test import BaseDatasetViewTest
from datahub.metadata.models import Team
from datahub.metadata.test.factories import TeamFactory


def get_expected_data_from_team(team):
    """Returns team data as a dictionary"""
    return {
        'country__name': team.country.name,
        'disabled_on': format_date_or_datetime(team.disabled_on),
        'id': str(team.id),
        'name': team.name,
        'role__name': team.role.name,
        'uk_region__name': team.uk_region.name,
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

    def test_with_updated_since_filter(self, data_flow_api_client):
        with freeze_time('2021-01-01 12:30:00'):
            TeamFactory()
        with freeze_time('2022-01-01 12:30:00'):
            team_after = TeamFactory()
        # Define the `updated_since` date
        updated_since_date = datetime(2021, 2, 1, tzinfo=utc).strftime('%Y-%m-%d')

        # Make the request with the `updated_since` parameter
        response = data_flow_api_client.get(self.view_url, {'updated_since': updated_since_date})

        assert response.status_code == status.HTTP_200_OK

        # Check that only contact created after the `updated_since` date are returned
        expected_ids = [str(team_after.id)]
        response_ids = [team['id'] for team in response.json()['results']]

        assert response_ids == expected_ids
