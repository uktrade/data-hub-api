import pytest
from django.urls import reverse
from rest_framework import status

from datahub.company.models import CompanyExportCountry
from datahub.company.test.factories import CompanyExportCountryFactory, CompanyFactory
from datahub.core.test.factories import to_many_field
from datahub.dataset.core.test import BaseDatasetViewTest
from datahub.metadata.models import Country


class CompanyWithFutureInterestCountriesFactory(CompanyFactory):
    """Overrides Company Factory to provide a future interest country"""

    @to_many_field
    def export_countries(self):
        """Return stubbed export countries"""
        return [
            CompanyExportCountryFactory(
                status=CompanyExportCountry.Status.FUTURE_INTEREST,
            ),
        ]


def get_expected_data_from_company(company):
    """
    Returns company export_countries data with status `future_interest`
    as a list of dictionaries
    """
    values = company.export_countries.filter(
        status=CompanyExportCountry.Status.FUTURE_INTEREST,
    ).values(
        'id',
        'company_id',
        'country__name',
        'country__iso_alpha2_code',
    )
    expected = []
    for value in values:
        expected.append(
            {
                'id': str(value['id']),
                'company_id': str(value['company_id']),
                'country__name': value['country__name'],
                'country__iso_alpha2_code': value['country__iso_alpha2_code'],
            },
        )
    expected = sorted(expected, key=lambda x: x['id'])
    return expected


@pytest.mark.django_db
class TestCompanyFutureinterestCountriesDatasetViewSet(BaseDatasetViewTest):
    """
    Tests for CompanyFutureInterestCountriesDatasetView
    """

    factory = CompanyWithFutureInterestCountriesFactory
    view_url = reverse('api-v4:dataset:company-future-interest-countries-dataset')

    @pytest.mark.parametrize(
        'company_factory', (
            CompanyFactory,
            CompanyWithFutureInterestCountriesFactory,
        ),
    )
    def test_company_with_no_interest(self, data_flow_api_client, company_factory):
        """Test that endpoint returns with expected data for a single company"""
        company = company_factory()
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']
        expected_result = get_expected_data_from_company(company)
        assert response_results == expected_result

    def test_with_multiple_records(self, data_flow_api_client):
        """Test that endpoint returns correct number of records"""
        countries = Country.objects.all()[:2]
        company1 = CompanyFactory()

        company2 = CompanyFactory()
        CompanyExportCountryFactory(
            company=company2,
            country=countries[0],
            status=CompanyExportCountry.Status.FUTURE_INTEREST,
        )

        company3 = CompanyFactory()
        CompanyExportCountryFactory(
            company=company3,
            country=countries[1],
            status=CompanyExportCountry.Status.FUTURE_INTEREST,
        )

        company4 = CompanyFactory()

        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']
        response_results = sorted(response_results, key=lambda x: x['id'])
        assert len(response_results) == 2

        companies = [company1, company2, company3, company4]
        expected_results = []
        for company in companies:
            expected_results.extend(get_expected_data_from_company(company))
        expected_results = sorted(expected_results, key=lambda x: x['id'])
        assert response_results == expected_results
