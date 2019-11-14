import factory
import pytest
from django.urls import reverse
from rest_framework import status

from datahub.company.models import Company
from datahub.company.test.factories import CompanyFactory
from datahub.core import constants
from datahub.core.test.factories import to_many_field
from datahub.dataset.core.test import BaseDatasetViewTest
from datahub.metadata.models import Country


class CompanyExportToCountriesFactory(factory.django.DjangoModelFactory):
    """Returns a company-export_to_country relationship"""

    company = factory.SubFactory(CompanyFactory)
    country_id = constants.Country.united_kingdom.value.id

    class Meta:
        model = Company.export_to_countries.through


class CompanyWithExportToCountriesFactory(CompanyFactory):
    """Extends Company Factory to provide a export_to_countries"""

    @to_many_field
    def export_to_countries(self):
        """Return stubbed countries"""
        return list(Country.objects.all()[:1])


def get_expected_data_from_company(company):
    """Returns company export_to_countries data as a list of dictionaries"""
    values = company.export_to_countries.through.objects.filter(
        company_id=company.id,
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
                'id': value['id'],
                'company_id': str(value['company_id']),
                'country__name': value['country__name'],
                'country__iso_alpha2_code': value['country__iso_alpha2_code'],
            },
        )
    expected = sorted(expected, key=lambda x: x['id'])
    return expected


@pytest.mark.django_db
class TestCompanyExportToCountriesDatasetViewSet(BaseDatasetViewTest):
    """
    Tests for CompanyExportToCountriesDatasetView
    """

    factory = CompanyExportToCountriesFactory
    view_url = reverse('api-v4:dataset:company-export-to-countries-dataset')

    @pytest.mark.parametrize(
        'company_factory', (
            CompanyFactory,
            CompanyWithExportToCountriesFactory,
        ),
    )
    def test_company_with_no_export_to_country(self, data_flow_api_client, company_factory):
        """Test that endpoint returns with expected data for a single company"""
        company = company_factory()
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']
        result = response_results
        expected_result = get_expected_data_from_company(company)
        assert result == expected_result

    def test_with_multiple_records(self, data_flow_api_client):
        """Test that endpoint returns correct number of records"""
        countries = Country.objects.all()[:3]
        company1 = CompanyFactory()
        company2 = CompanyFactory(export_to_countries=countries[:2])
        company3 = CompanyFactory(export_to_countries=countries[:1])
        company4 = CompanyFactory()
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']
        assert len(response_results) == 3

        companies = [company1, company2, company3, company4]
        expected_results = []
        for company in companies:
            expected_results.extend(get_expected_data_from_company(company))
        expected_results = sorted(expected_results, key=lambda x: x['id'])
        assert response_results == expected_results
