import pytest

from django.urls import reverse

from datahub.core.test_utils import (
    format_date_or_datetime,
)
from datahub.dataset.core.test import BaseDatasetViewTest
from datahub.export_win.test.factories import WinAdviserFactory


@pytest.mark.django_db
class TestExportWinsAdvisersDatasetView(BaseDatasetViewTest):
    view_url = reverse('api-v4:dataset:export-wins-advisers-dataset')
    factory = WinAdviserFactory

    def test_response_for_empty_dataset(self, data_flow_api_client):
        response = data_flow_api_client.get(self.view_url).json()

        assert response['results'] == []
        assert response['next'] is None
        assert response['previous'] is None

    def test_response_for_single_dataset(self, data_flow_api_client):

        win_adviser = WinAdviserFactory(location='Somewhere', name='bob')

        response = data_flow_api_client.get(self.view_url).json()

        assert response['results'][0] == {
            'created_on': format_date_or_datetime(win_adviser.created_on),
            'id': win_adviser.legacy_id,
            'location': win_adviser.location,
            'name': win_adviser.name,
            'win__id': str(win_adviser.win.id),
            'hq_team_display': win_adviser.hq_team.name,
            'team_type_display': win_adviser.team_type.name,
            'hq_team': win_adviser.hq_team.export_win_id,
            'team_type': win_adviser.team_type.export_win_id,
        }
        assert response['next'] is None
        assert response['previous'] is None
