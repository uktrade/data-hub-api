from datetime import datetime

import pytest
from dateutil import parser
from django.utils.timezone import utc
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import CompanyExportCountryHistoryFactory, CompanyFactory
from datahub.core.test_utils import (
    APITestMixin,
    create_test_user,
)
from datahub.metadata.models import Country
from datahub.metadata.test.factories import TeamFactory
from datahub.search.exportcountryhistory import ExportCountryHistoryApp

pytestmark = [
    pytest.mark.django_db,
    # Index objects for this search app only
    pytest.mark.es_collector_apps.with_args(ExportCountryHistoryApp),
]

FROZEN_DATETIME_1 = datetime(2001, 1, 24, 1, 2, 3, tzinfo=utc)
FROZEN_DATETIME_2 = datetime(2002, 1, 24, 1, 2, 3, tzinfo=utc)
FROZEN_DATETIME_3 = datetime(2003, 1, 24, 1, 2, 3, tzinfo=utc)

AUSTRALIA_UUID = '9f5f66a0-5d95-e211-a939-e4115bead28a'
ECUADOR_UUID = '75af72a6-5d95-e211-a939-e4115bead28a'
COMPANY_UUID = 'f9ea83a6-41d7-11ea-a185-3c15c2e46112'


@pytest.fixture
def setup_data():
    """Sets up data for the tests."""
    benchmark_country_australia = list(Country.objects.filter(
        id=AUSTRALIA_UUID,
    ))[0]

    benchmark_country_ecuador = list(Country.objects.filter(
        id=ECUADOR_UUID,
    ))[0]

    benchmark_company = CompanyFactory(
        id='f9ea83a6-41d7-11ea-a185-3c15c2e46112',
    )

    export_country_history_items = []

    with freeze_time(FROZEN_DATETIME_1):
        export_country_history_items.append([
            CompanyExportCountryHistoryFactory(
                country=benchmark_country_australia,
                company=benchmark_company,
            ),
            CompanyExportCountryHistoryFactory(
                company=benchmark_company,
                country=benchmark_country_ecuador,
            ),
            CompanyExportCountryHistoryFactory(
                country=benchmark_country_ecuador,
            ),
            CompanyExportCountryHistoryFactory(),
        ])

    with freeze_time(FROZEN_DATETIME_2):
        export_country_history_items.append([
            CompanyExportCountryHistoryFactory(
                country=benchmark_country_australia,
            ),
        ])

    with freeze_time(FROZEN_DATETIME_3):
        export_country_history_items.append([
            CompanyExportCountryHistoryFactory(
                country=benchmark_country_australia,
            ),
        ])

    yield export_country_history_items


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

        url = reverse('api-v4:search:export-country-history')

        response = self.api_client.post(
            url,
            data={},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.parametrize(
        'request_data,expected_status,expected_count,expected_data',
        (
            (
                {
                    'country': AUSTRALIA_UUID,
                },
                status.HTTP_200_OK,
                3,
                {
                    'country': {
                        'id': AUSTRALIA_UUID,
                    },
                },
            ),
            (
                {
                    'company': COMPANY_UUID,
                },
                status.HTTP_200_OK,
                2,
                {
                    'company': {
                        'id': COMPANY_UUID,
                    },
                },
            ),
            (
                {
                    'company': COMPANY_UUID,
                    'country': ECUADOR_UUID,
                },
                status.HTTP_200_OK,
                1,
                {
                    'company': {
                        'id': COMPANY_UUID,
                    },
                    'country': {
                        'id': ECUADOR_UUID,
                    },
                },
            ),
        ),
    )
    def test_export_country_history_search(
        self,
        es_with_collector,
        request_data,
        expected_status,
        expected_count,
        expected_data,
        setup_data,
    ):
        """
        Test ExportCountryHistory search app with country and/or company param.
        """
        es_with_collector.flush_and_refresh()

        url = reverse('api-v4:search:export-country-history')

        response = self.api_client.post(
            url,
            data=request_data,
        )

        assert response.status_code == expected_status
        assert response.data['count'] == expected_count
        for key, _value in expected_data.items():
            assert any(
                data[key]['id'] == expected_data[key]['id'] for data in response.data['results']
            )

    def test_sorting_in_export_country_history(self, es_with_collector, setup_data):
        """Tests the sorting of country history search response."""
        es_with_collector.flush_and_refresh()

        url = reverse('api-v4:search:export-country-history')

        response = self.api_client.post(
            url,
            data={
                'country': AUSTRALIA_UUID,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 3

        date_times = [
            parser.parse(_['history_date']) for _ in response.data['results']
        ]

        assert date_times == [FROZEN_DATETIME_3, FROZEN_DATETIME_2, FROZEN_DATETIME_1]
