import pytest
from django.conf import settings
from django.urls import reverse
from rest_framework import status

from datahub.company.test.factories import (
    ArchivedCompanyFactory,
    CompanyFactory,
)
from datahub.core.test_utils import HawkAPITestClient
from datahub.metadata.models import Country


@pytest.fixture
def hawk_api_client():
    """Hawk API client fixture."""
    yield HawkAPITestClient()


@pytest.fixture
def data_flow_api_client(hawk_api_client):
    """Hawk API client fixture configured to use credentials with the data_flow_api scope."""
    hawk_api_client.set_credentials(
        'data-flow-api-id',
        'data-flow-api-key',
    )
    yield hawk_api_client


def get_expected_data_from_company(company):
    """Returns company future interest countries data as a list of dictionaries"""
    future_interest_countries = company.future_interest_countries.all()
    if len(future_interest_countries) == 0:
        return [
            {
                'id': str(company.id),
                'future_interest_countries__name': None,
                'future_interest_countries__iso_alpha2_code': None,
            },
        ]
    else:
        expected = []
        for future_interest_country in future_interest_countries:
            x = {
                'id': str(company.id),
                'future_interest_countries__name': future_interest_country.name,
                'future_interest_countries__iso_alpha2_code':
                future_interest_country.iso_alpha2_code,
            }
            expected.append(x)
        return expected


@pytest.mark.django_db
class TestCompaniesDatasetViewSet:
    """
    Tests for CompanyFutureInterestCountriesDatasetView
    """

    view_url = reverse('api-v4:dataset:company-future-interest-countries-dataset')

    @pytest.mark.parametrize('method', ('delete', 'patch', 'post', 'put'))
    def test_other_methods_not_allowed(
        self,
        data_flow_api_client,
        method,
    ):
        """Test that various HTTP methods are not allowed."""
        response = data_flow_api_client.request(method, self.view_url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_without_scope(self, hawk_api_client):
        """Test that making a request without the correct Hawk scope returns an error."""
        hawk_api_client.set_credentials(
            'test-id-without-scope',
            'test-key-without-scope',
        )
        response = hawk_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_without_credentials(self, api_client):
        """Test that making a request without credentials returns an error."""
        response = api_client.get(self.view_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize(
        'company_factory', (
            CompanyFactory,
            ArchivedCompanyFactory,
        ),
    )
    def test_company_with_no_interest(self, data_flow_api_client, company_factory):
        """Test that endpoint returns with expected data for a single company"""
        company = company_factory()
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']
        assert len(response_results) == 1
        result = response_results
        expected_result = get_expected_data_from_company(company)
        assert result == expected_result

    def test_company_with_interest(self, data_flow_api_client):
        """Test that endpoint returns with expected data for a single company"""
        countries = Country.objects.all()[:1]
        company = CompanyFactory(future_interest_countries=countries)
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']
        assert len(response_results) == 1
        result = response_results
        expected_result = get_expected_data_from_company(company)
        assert result == expected_result

    def test_company_with_multiple_interests(self, data_flow_api_client):
        """Test that endpoint returns with expected data for a single company"""
        countries = Country.objects.all()[:2]
        company = CompanyFactory(future_interest_countries=[countries[0], countries[1]])
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']
        assert len(response_results) == 2
        result = response_results
        expected_result = get_expected_data_from_company(company)
        assert result == expected_result

    def test_with_multiple_records(self, data_flow_api_client):
        """Test that endpoint returns correct number of records"""
        countries = Country.objects.all()[:3]
        company1 = CompanyFactory()
        company2 = CompanyFactory(future_interest_countries=countries[:2])
        company3 = CompanyFactory(future_interest_countries=countries[:1])
        company4 = CompanyFactory()
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']
        assert len(response_results) == 5

        sorted_companies = sorted([company1, company2, company3, company4], key=lambda x: x.id)
        expected_results = []
        for company in sorted_companies:
            expected_results.extend(get_expected_data_from_company(company))
        assert response_results == expected_results

    def test_pagination(self, data_flow_api_client):
        """Test that when page size higher than threshold response returns with next page url"""
        CompanyFactory.create_batch(settings.REST_FRAMEWORK['PAGE_SIZE'] + 1)
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['next'] is not None

    def test_no_data(self, data_flow_api_client):
        """Test that without any data available, endpoint completes the request successfully"""
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
