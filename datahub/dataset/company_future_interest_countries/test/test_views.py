import pytest
from django.urls import reverse
from freezegun import freeze_time
from rest_framework import status

from datahub.company.models import CompanyExportCountry
from datahub.company.test.factories import CompanyExportCountryFactory
from datahub.core.test_utils import format_date_or_datetime
from datahub.dataset.core.test import BaseDatasetViewTest


class FutureInterestExportCountryFactory(CompanyExportCountryFactory):
    """Future interest company export country."""

    status = CompanyExportCountry.Status.FUTURE_INTEREST


def get_expected_data_from_export_country(export_country):
    """
    Returns company export_countries data with status `future_interest`
    as a list of dictionaries
    """
    return {
        'id': str(export_country.pk),
        'company_id': str(export_country.company_id),
        'country__name': export_country.country.name,
        'country__iso_alpha2_code': export_country.country.iso_alpha2_code,
        'created_on': format_date_or_datetime(export_country.created_on),
    }


@pytest.mark.django_db
class TestCompanyFutureInterestCountriesDatasetViewSet(BaseDatasetViewTest):
    """
    Tests for CompanyFutureInterestCountriesDatasetView
    """

    factory = FutureInterestExportCountryFactory
    view_url = reverse('api-v4:dataset:company-future-interest-countries-dataset')

    def test_response_body(self, data_flow_api_client):
        """Test that endpoint returns the expected data for a single export country."""
        export_country = self.factory()
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']
        assert len(response_results) == 1
        result = response_results[0]
        expected_result = get_expected_data_from_export_country(export_country)
        assert result == expected_result

    @pytest.mark.parametrize(
        'export_country_status',
        (
            CompanyExportCountry.Status.CURRENTLY_EXPORTING,
            CompanyExportCountry.Status.NOT_INTERESTED,
        ),
    )
    def test_excludes_other_statuses(self, data_flow_api_client, export_country_status):
        """Test that endpoint excludes other export country statuses."""
        CompanyExportCountry(status=export_country_status)
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['results'] == []

    def test_with_multiple_records(self, data_flow_api_client):
        """Test the ordering of results."""
        with freeze_time('2019-01-01 12:30:00'):
            export_country_1 = self.factory()
        with freeze_time('2019-01-03 12:00:00'):
            export_country_2 = self.factory()
        with freeze_time('2019-01-01 12:00:00'):
            export_country_3 = self.factory()
            export_country_4 = self.factory()

        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']
        assert len(response_results) == 4
        expected_results = [
            *sorted([export_country_3, export_country_4], key=lambda x: x.pk),
            export_country_1,
            export_country_2,
        ]
        for index, export_country in enumerate(expected_results):
            assert str(export_country.id) == response_results[index]['id']
