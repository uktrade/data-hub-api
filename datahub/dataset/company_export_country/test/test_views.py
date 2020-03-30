import pytest
from django.urls import reverse
from freezegun import freeze_time

from datahub.company.test.factories import CompanyExportCountryFactory
from datahub.dataset.core.test import BaseDatasetViewTest


def get_expected_data_from_company_export_country(company_export_country):
    """Returns company_export_country data as a dictionary"""
    return {
        'id': str(company_export_country.id),
        'company_id': str(company_export_country.company_id),
        'country__name': company_export_country.country.name,
        'country__iso_alpha2_code': company_export_country.country.iso_alpha2_code,
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
                company_export_country_1,
                company_export_country_2,
                company_export_country_3,
                company_export_country_4,
            ],
            key=lambda x: x.id,
        )

        for i in range(len(expected_list)):
            assert response_results[i]['id'] == str(expected_list[i].id)
