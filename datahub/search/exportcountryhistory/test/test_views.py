import factory
import pytest
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


@pytest.fixture
def setup_data():
    """Sets up data for the tests."""
    benchmark_country = list(Country.objects.filter(
        id='9f5f66a0-5d95-e211-a939-e4115bead28a',  # Australia
    ))[0]
    benchmark_company = factory.SubFactory(CompanyFactory)

    export_country_history_items = [
        CompanyExportCountryHistoryFactory(
            country=benchmark_country,
            company=benchmark_company,
        ),
        CompanyExportCountryHistoryFactory(),
    ]
    yield export_country_history_items


class TestSearch(APITestMixin):
    """Tests search views."""

    def test_export_country_history_search_no_permissions(self):
        """Should return 403"""
        user = create_test_user(dit_team=TeamFactory())
        api_client = self.create_api_client(user=user)
        url = reverse('api-v4:search:export-country-history')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_search_country_in_export_country_history(self, es_with_collector, setup_data):
        """Tests export country history search."""
        es_with_collector.flush_and_refresh()

        country = list(Country.objects.order_by('?')[:1])[0]
        date = factory.Faker('date_object')

        CompanyExportCountryHistoryFactory(
            country=country,
            history_date=date,
            company=factory.SubFactory(CompanyFactory),
        )
        CompanyExportCountryHistoryFactory()

        url = reverse('api-v4:search:export-country-history')

        response = self.api_client.post(
            url,
            data={
                'country': 'Australia',
                'date': '2020-01-17T19:49:39.900994+00:00',
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] > 0
