from datetime import datetime

import pytest

from django.urls import reverse

from django.utils.timezone import utc

from freezegun import freeze_time

from rest_framework import status


from datahub.company.test.factories import CompanyExportCountryFactory
from datahub.core.test_utils import format_date_or_datetime
from datahub.dataset.core.test import BaseDatasetViewTest


def get_expected_data_from_company_export_country(company_export_country):
    """Returns company_export_country data as a dictionary"""
    return {
        'id': str(company_export_country.id),
        'company_id': str(company_export_country.company_id),
        'country__name': company_export_country.country.name,
        'country__iso_alpha2_code': company_export_country.country.iso_alpha2_code,
        'created_on': format_date_or_datetime(company_export_country.created_on),
        'modified_on': format_date_or_datetime(company_export_country.modified_on),
        'status': company_export_country.status,
    }


@pytest.mark.django_db
class TestCompanyExportCountryDatasetView(BaseDatasetViewTest):
    """
    Tests for CompanyExportCountryDatasetView
    """

    factory = CompanyExportCountryFactory
    view_url = reverse('api-v4:dataset:company-export-country-dataset')

    def test_success(self, data_flow_api_client):
        """Test that endpoint returns with expected data for a single event"""
        company_export_country = self.factory()
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == 200
        response_results = response.json()['results']
        assert len(response_results) == 1
        result = response_results[0]

        expected_result = get_expected_data_from_company_export_country(company_export_country)

        assert result == expected_result

    def test_with_multiple_events(self, data_flow_api_client):
        """Test that endpoint returns correct order of event records"""
        with freeze_time('2019-01-01 12:30:00'):
            company_export_country_1 = self.factory()
        with freeze_time('2019-01-03 12:00:00'):
            company_export_country_2 = self.factory()
        with freeze_time('2019-01-01 12:00:00'):
            company_export_country_3 = self.factory()
            company_export_country_4 = self.factory()
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == 200
        response_results = response.json()['results']
        assert len(response_results) == 4

        expected_list = sorted(
            [
                company_export_country_3,
                company_export_country_4,
            ],
            key=lambda x: x.id,
        ) + [company_export_country_1, company_export_country_2]

        for i in range(len(expected_list)):
            assert response_results[i]['id'] == str(expected_list[i].id)

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
