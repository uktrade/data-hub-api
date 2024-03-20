import pytest

from django.urls import reverse

from datahub.core.test_utils import (
    format_date_or_datetime,
)
from datahub.dataset.core.test import BaseDatasetViewTest
from datahub.export_win.test.factories import BreakdownFactory, WinAdviserFactory


pytestmark = pytest.mark.django_db


class TestExportWinsAdvisersDatasetView(BaseDatasetViewTest):
    view_url = reverse('api-v4:dataset:export-wins-advisers-dataset')
    factory = WinAdviserFactory

    def _assert_win_adviser_matches_result(self, win_adviser, result):
        assert result == {
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

    def test_success(self, data_flow_api_client):

        win_adviser = self.factory(location='Somewhere', name='bob')

        response = data_flow_api_client.get(self.view_url).json()

        assert len(response['results']) == 1
        self._assert_win_adviser_matches_result(win_adviser, response['results'][0])

    def test_with_multiple_win_adviser(self, data_flow_api_client):

        win_advisers = self.factory.create_batch(3)

        response = data_flow_api_client.get(self.view_url).json()

        assert len(response['results']) == 3
        for i, result in enumerate(response['results']):
            self._assert_win_adviser_matches_result(win_advisers[i], result)


class TestExportWinsBreakdownDatasetView(BaseDatasetViewTest):
    view_url = reverse('api-v4:dataset:export-wins-breakdowns-dataset')
    factory = BreakdownFactory

    def _assert_win_adviser_matches_result(self, breakdown, result):
        assert result == {
            'created_on': format_date_or_datetime(breakdown.created_on),
            'id': breakdown.legacy_id,
            'win__id': str(breakdown.win.id),
            'year': breakdown.year,
            'value': breakdown.value,
            'breakdown_type': breakdown.type.name,
        }

    def test_success(self, data_flow_api_client):

        win_adviser = self.factory()

        response = data_flow_api_client.get(self.view_url).json()

        assert len(response['results']) == 1
        self._assert_win_adviser_matches_result(win_adviser, response['results'][0])

    def test_with_multiple_win_adviser(self, data_flow_api_client):

        win_advisers = self.factory.create_batch(3)

        response = data_flow_api_client.get(self.view_url).json()

        assert len(response['results']) == 3
        for i, result in enumerate(response['results']):
            self._assert_win_adviser_matches_result(win_advisers[i], result)
