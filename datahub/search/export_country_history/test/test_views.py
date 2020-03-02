from datetime import datetime

import pytest
from django.utils.timezone import utc
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.models import CompanyExportCountryHistory
from datahub.company.test.factories import CompanyExportCountryHistoryFactory, CompanyFactory
from datahub.core.constants import Country as CountryConstant
from datahub.core.test_utils import (
    APITestMixin,
    create_test_user,
)
from datahub.interaction.test.factories import (
    ExportCountriesInteractionFactory,
    InteractionExportCountryFactory,
)
from datahub.metadata.models import Country
from datahub.metadata.test.factories import TeamFactory
from datahub.search.export_country_history import ExportCountryHistoryApp
from datahub.search.interaction import InteractionSearchApp

pytestmark = [
    pytest.mark.django_db,
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
            history_type=CompanyExportCountryHistory.HistoryType.INSERT,
        )
        CompanyExportCountryHistoryFactory(
            company=benchmark_company,
            country=benchmark_country_canada,
            history_type=CompanyExportCountryHistory.HistoryType.INSERT,
        )
        CompanyExportCountryHistoryFactory(
            country=benchmark_country_canada,
            history_type=CompanyExportCountryHistory.HistoryType.DELETE,
        )
        # will be excluded, because of UPDATE
        CompanyExportCountryHistoryFactory(
            country=benchmark_country_japan,
            company=benchmark_company,
            history_type=CompanyExportCountryHistory.HistoryType.UPDATE,
        )

        ExportCountriesInteractionFactory(
            company=benchmark_company,
            were_countries_discussed=True,
            export_countries__country=benchmark_country_canada,
            date=FROZEN_DATETIME_1,
        )
        # will be excluded as were_countries_discussed is False
        ExportCountriesInteractionFactory(
            company=benchmark_company,
            were_countries_discussed=False,
            date=FROZEN_DATETIME_1,
        )
        ExportCountriesInteractionFactory(
            were_countries_discussed=True,
            export_countries__country=benchmark_country_japan,
            date=FROZEN_DATETIME_1,
        )

    with freeze_time(FROZEN_DATETIME_2):
        CompanyExportCountryHistoryFactory(
            country=benchmark_country_japan,
            history_type=CompanyExportCountryHistory.HistoryType.INSERT,
        )
        CompanyExportCountryHistoryFactory(
            company=benchmark_company,
            country=benchmark_country_canada,
            history_type=CompanyExportCountryHistory.HistoryType.INSERT,
        )
        CompanyExportCountryHistoryFactory(
            company=benchmark_company,
            country=benchmark_country_japan,
            history_type=CompanyExportCountryHistory.HistoryType.DELETE,
        )
        # will be excluded, because of UPDATE
        CompanyExportCountryHistoryFactory(
            country=benchmark_country_canada,
            company=benchmark_company,
            history_type=CompanyExportCountryHistory.HistoryType.UPDATE,
        )

        ExportCountriesInteractionFactory(
            company=benchmark_company,
            were_countries_discussed=True,
            export_countries__country=benchmark_country_japan,
            date=FROZEN_DATETIME_2,
        )
        # will be excluded as were_countries_discussed is False
        ExportCountriesInteractionFactory(
            company=benchmark_company,
            were_countries_discussed=False,
            date=FROZEN_DATETIME_2,
        )
        ExportCountriesInteractionFactory(
            were_countries_discussed=True,
            export_countries__country=benchmark_country_canada,
            date=FROZEN_DATETIME_2,
        )

    with freeze_time(FROZEN_DATETIME_3):
        CompanyExportCountryHistoryFactory(
            country=benchmark_country_canada,
            history_type=CompanyExportCountryHistory.HistoryType.INSERT,
            history_user=None,
        )
        CompanyExportCountryHistoryFactory(
            company=benchmark_company,
            country=benchmark_country_japan,
            history_type=CompanyExportCountryHistory.HistoryType.DELETE,
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

    @pytest.mark.parametrize(
        'history_type,count',
        (
            (CompanyExportCountryHistory.HistoryType.INSERT, 1),
            (CompanyExportCountryHistory.HistoryType.DELETE, 1),
            (CompanyExportCountryHistory.HistoryType.UPDATE, 0),
        ),
    )
    def test_filtering_by_only_export_country_history_by_company(
        self,
        es_with_collector,
        history_type,
        count,
    ):
        """
        Check search works when there are only export country history, no interactions.
        """
        benchmark_country_canada = Country.objects.get(
            pk=CountryConstant.canada.value.id,
        )
        benchmark_company = CompanyFactory()
        CompanyExportCountryHistoryFactory(
            company=benchmark_company,
            country=benchmark_country_canada,
            history_type=history_type,
        )

        es_with_collector.flush_and_refresh()

        url = reverse('api-v4:search:export-country-history')
        company_id = str(benchmark_company.id)

        response = self.api_client.post(
            url,
            data={
                'company': company_id,
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['count'] == count
        assert all(
            result['company']['id'] == company_id
            for result in response.json()['results']
        )

    @pytest.mark.parametrize(
        'countries_discussed,count',
        (
            (True, 1),
            (False, 0),
        ),
    )
    def test_filter_only_interactions_by_company(
        self,
        es_with_collector,
        countries_discussed,
        count,
    ):
        """
        Check search works when there are only interactions, no export country history.
        """
        benchmark_country_canada = Country.objects.get(
            pk=CountryConstant.canada.value.id,
        )
        benchmark_company = CompanyFactory()

        interaction = ExportCountriesInteractionFactory(
            company=benchmark_company,
            were_countries_discussed=countries_discussed,
        )
        if countries_discussed:
            interaction.export_countries.set([
                InteractionExportCountryFactory(
                    country=benchmark_country_canada,
                ),
            ])

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
        assert response.json()['count'] == count
        assert all(
            result['company']['id'] == company_id
            for result in response.json()['results']
        )

    def test_all_history_filtering_by_company(
        self,
        es_with_collector,
        setup_data,
    ):
        """
        Test ExportCountryHistory, along with interactions
        search app with company param.
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
        assert response.json()['count'] == 7
        assert all(
            result['company']['id'] == expected_data['company']['id']
            for result in response.json()['results']
        )

        date_times = [
            result['date'] for result in response.json()['results']
        ]
        assert date_times == [
            FROZEN_DATETIME_3,
            FROZEN_DATETIME_2,
            FROZEN_DATETIME_2,
            FROZEN_DATETIME_2,
            FROZEN_DATETIME_1,
            FROZEN_DATETIME_1,
            FROZEN_DATETIME_1,
        ]

    def test_all_history_filtering_by_company_and_country(
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
        assert response.json()['count'] == 3
        assert all(
            result['company']['id'] == expected_data['company']['id']
            for result in response.json()['results']
        )
        for result in response.json()['results']:
            if result.get('kind', '') == 'interaction':
                result_countries = [item['country']['id'] for item in result['export_countries']]
                assert expected_data['country']['id'] in result_countries
        assert all(
            result['country']['id'] == expected_data['country']['id']
            for result in response.json()['results']
            if result.get('kind', '') != 'interaction'
        )

    def test_filtering_by_country(
        self,
        es_with_collector,
        setup_data,
    ):
        """
        Test ExportCountryHistory search app with country param.
        Not a real life usecase, but still good to check.
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
        assert response.json()['count'] == 6
        for result in response.json()['results']:
            if result.get('kind', '') == 'interaction':
                result_countries = [item['country']['id'] for item in result['export_countries']]
                assert expected_data['country']['id'] in result_countries
        assert all(
            result['country']['id'] == expected_data['country']['id']
            for result in response.json()['results']
            if result.get('kind', '') != 'interaction'
        )

        date_times = [
            result['date'] for result in response.json()['results']
        ]
        assert date_times == [
            FROZEN_DATETIME_3,
            FROZEN_DATETIME_2,
            FROZEN_DATETIME_2,
            FROZEN_DATETIME_2,
            FROZEN_DATETIME_1,
            FROZEN_DATETIME_1,
        ]
