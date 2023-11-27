from datetime import datetime

import pytest

from django.urls import reverse

from django.utils.timezone import utc

from freezegun import freeze_time
from rest_framework import status

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

    def test_with_updated_since_filter(self, data_flow_api_client):
        with freeze_time('2021-01-01 12:30:00'):
            self.factory()
        with freeze_time('2022-01-01 12:30:00'):
            company_export_after = self.factory()
        # Define the `updated_since` date
        updated_since_date = datetime(2021, 2, 1, tzinfo=utc).strftime('%Y-%m-%d')

        # Make the request with the `updated_since` parameter
        response = data_flow_api_client.get(self.view_url, {'updated_since': updated_since_date})

        assert response.status_code == status.HTTP_200_OK

        # Check that only companies created after the `updated_since` date are returned
        expected_ids = [str(company_export_after.id)]
        response_ids = [company['id'] for company in response.json()['results']]

        assert response_ids == expected_ids
