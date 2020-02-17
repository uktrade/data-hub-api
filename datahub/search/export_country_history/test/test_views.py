from datetime import datetime

import pytest
from django.utils.timezone import utc
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.models import CompanyExportCountry, CompanyExportCountryHistory
from datahub.company.test.factories import CompanyExportCountryHistoryFactory, CompanyFactory
from datahub.core.constants import Country as CountryConstant
from datahub.core.test_utils import (
    APITestMixin,
    create_test_user,
)
from datahub.interaction.test.factories import CompanyInteractionFactory, ExportCountriesInteractionFactory
from datahub.metadata.models import Country
from datahub.metadata.test.factories import TeamFactory
from datahub.search.interaction import InteractionSearchApp
from datahub.search.export_country_history import ExportCountryHistoryApp

pytestmark = [
    pytest.mark.django_db,
    # Index objects for this search app only
    pytest.mark.es_collector_apps.with_args(ExportCountryHistoryApp, InteractionSearchApp),
]

FROZEN_DATETIME_1 = datetime(2001, 1, 22, 1, 2, 3, tzinfo=utc).isoformat()
FROZEN_DATETIME_2 = datetime(2002, 2, 23, 4, 5, 6, tzinfo=utc).isoformat()
FROZEN_DATETIME_3 = datetime(2003, 3, 24, 7, 8, 9, tzinfo=utc).isoformat()


@pytest.fixture
def setup_data():
    """Sets up data for the tests."""
    benchmark_country_japan = Country.objects.get(
        pk=CountryConstant.japan.value.id,
    )

    benchmark_country_canada = Country.objects.get(
        pk=CountryConstant.canada.value.id,
    )

    benchmark_company = CompanyFactory()

    with freeze_time(FROZEN_DATETIME_1):
        CompanyExportCountryHistoryFactory(
            country=benchmark_country_japan,
            company=benchmark_company,
        )
        CompanyExportCountryHistoryFactory(
            company=benchmark_company,
            country=benchmark_country_canada,
        )
        CompanyExportCountryHistoryFactory(
            country=benchmark_country_canada,
        )
        CompanyExportCountryHistoryFactory()

    with freeze_time(FROZEN_DATETIME_2):
        CompanyExportCountryHistoryFactory(
            country=benchmark_country_japan,
        )

    with freeze_time(FROZEN_DATETIME_3):
        CompanyExportCountryHistoryFactory(
            country=benchmark_country_japan,
        )

    yield str(benchmark_company.id)


class TestSearchExportCountryHistory(APITestMixin):
    """Tests search views."""

    def test_export_country_history_search_no_permissions(self):
        """Should return 403"""
        user = create_test_user(dit_team=TeamFactory())
        api_client = self.create_api_client(user=user)
        url = reverse('api-v4:search:export-country-history')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_export_country_history_search_with_empty_request(self, es_with_collector, setup_data):
        """Should return 400."""
        es_with_collector.flush_and_refresh()
        error_response = 'Request must include either country or company parameters'

        url = reverse('api-v4:search:export-country-history')

        response = self.api_client.post(
            url,
            data={},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()['non_field_errors'][0] == error_response

    def test_filtering_by_country_on_export_country_history_search(
        self,
        es_with_collector,
        setup_data,
    ):
        """
        Test ExportCountryHistory search app with country param.
        """
        es_with_collector.flush_and_refresh()

        url = reverse('api-v4:search:export-country-history')

        response = self.api_client.post(
            url,
            data={
                'country': CountryConstant.japan.value.id,
            },
        )

        expected_data = {
            'country': {
                'id': CountryConstant.japan.value.id,
            },
        }

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['count'] == 3
        assert all(
            result['country']['id'] == expected_data['country']['id']
            for result in response.json()['results']
        )

    def test_filtering_by_company_on_export_country_history_search(
        self,
        es_with_collector,
        setup_data,
    ):
        """
        Test ExportCountryHistory search app with company param.
        """
        es_with_collector.flush_and_refresh()

        url = reverse('api-v4:search:export-country-history')
        company_id = setup_data

        response = self.api_client.post(
            url,
            data={
                'company': company_id,
            },
        )

        expected_data = {
            'company': {
                'id': company_id,
            },
        }

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['count'] == 2
        assert all(
            result['company']['id'] == expected_data['company']['id']
            for result in response.json()['results']
        )

    def test_filtering_by_company_and_country_on_export_country_history_search(
        self,
        es_with_collector,
        setup_data,
    ):
        """
        Test ExportCountryHistory search app with company param.
        """
        es_with_collector.flush_and_refresh()

        url = reverse('api-v4:search:export-country-history')

        response = self.api_client.post(
            url,
            data={
                'company': setup_data,
                'country': CountryConstant.canada.value.id,
            },
        )

        expected_data = {
            'company': {
                'id': setup_data,
            },
            'country': {
                'id': CountryConstant.canada.value.id,
            },
        }

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['count'] == 1
        assert all(
            result['company']['id'] == expected_data['company']['id']
            for result in response.json()['results']
        )
        assert all(
            result['country']['id'] == expected_data['country']['id']
            for result in response.json()['results']
        )

    def test_sorting_in_export_country_history(self, es_with_collector, setup_data):
        """Tests the sorting of country history search response."""
        es_with_collector.flush_and_refresh()

        url = reverse('api-v4:search:export-country-history')

        response = self.api_client.post(
            url,
            data={
                'country': CountryConstant.japan.value.id,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['count'] == 3

        date_times = [
            result['history_date'] for result in response.json()['results']
        ]

        assert date_times == [FROZEN_DATETIME_3, FROZEN_DATETIME_2, FROZEN_DATETIME_1]

    def test_export_country_history_search_interactions_by_company(self, es_with_collector):
        benchmark_country_canada = Country.objects.get(
            pk=CountryConstant.canada.value.id,
        )
        benchmark_company = CompanyFactory()

        ExportCountriesInteractionFactory(
            company=benchmark_company,
            export_countries__country=benchmark_country_canada,
            export_countries__status=CompanyExportCountry.Status.NOT_INTERESTED,
        )
        es_with_collector.flush_and_refresh()
        company_id = str(benchmark_company.id)

        url = reverse('api-v4:search:export-country-history')

        response = self.api_client.post(
            url,
            data={
                'company': company_id,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['count'] == 1
        assert all(
            result['company']['id'] == company_id
            for result in response.json()['results']
        )
