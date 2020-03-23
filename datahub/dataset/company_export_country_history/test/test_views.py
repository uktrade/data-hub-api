import pytest
from django.urls import reverse
from freezegun import freeze_time

from datahub.company.test.factories import CompanyExportCountryHistoryFactory
from datahub.core.test_utils import format_date_or_datetime
from datahub.dataset.core.test import BaseDatasetViewTest


def get_expected_data_from_export_country_history(export_country_history):
    """Returns export_country_history data as a dictionary"""
    return {
        'id': str(export_country_history.id),
        'company_id': str(export_country_history.company_id),
        'country__name': export_country_history.country.name,
        'country__iso_alpha2_code': export_country_history.country.iso_alpha2_code,
        'history_date': format_date_or_datetime(export_country_history.history_date),
        'history_id': str(export_country_history.history_id),
        'history_type': export_country_history.history_type,
        'status': export_country_history.status,
    }


@pytest.mark.django_db
class TestCompanyExportCountryHistoryDatasetView(BaseDatasetViewTest):
    """
    Tests for CompanyExportCountryHistoryDatasetView
    """

    factory = CompanyExportCountryHistoryFactory
    view_url = reverse('api-v4:dataset:company-export-country-history-dataset')

    def test_success(self, data_flow_api_client):
        """Test that endpoint returns with expected data for a single event"""
        export_country_history = self.factory()
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == 200
        response_results = response.json()['results']
        assert len(response_results) == 1
        result = response_results[0]

        expected_result = get_expected_data_from_export_country_history(export_country_history)

        assert result == expected_result

    def test_with_multiple_events(self, data_flow_api_client):
        """Test that endpoint returns correct order of event records"""
        with freeze_time('2019-01-01 12:30:00'):
            export_country_history_1 = self.factory()
        with freeze_time('2019-01-03 12:00:00'):
            export_country_history_2 = self.factory()
        with freeze_time('2019-01-01 12:00:00'):
            export_country_history_3 = self.factory()
            export_country_history_4 = self.factory()
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == 200
        response_results = response.json()['results']
        assert len(response_results) == 4

        expected_list = sorted(
            [
                export_country_history_3,
                export_country_history_4,
            ],
            key=lambda x: x.history_id,
        ) + [export_country_history_1, export_country_history_2]

        for i in range(len(expected_list)):
            assert response_results[i]['history_id'] == str(expected_list[i].history_id)
