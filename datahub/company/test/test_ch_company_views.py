import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import CompaniesHouseCompanyFactory
from datahub.core.test_utils import APITestMixin, format_date_or_datetime


class TestCHCompany(APITestMixin):
    """CH company tests."""

    def test_list(self):
        """Test listing CH companies."""
        companies = CompaniesHouseCompanyFactory.create_batch(2)

        url = reverse('api-v4:ch-company:collection')
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == len(companies)

        actual_ids = {result['id'] for result in response_data['results']}
        expected_ids = {company.id for company in companies}
        assert actual_ids == expected_ids

    @pytest.mark.parametrize('company_number', ('123456789', 'SC00001234'))
    def test_get(self, company_number):
        """Test retrieving a single CH company."""
        ch_company = CompaniesHouseCompanyFactory(
            company_number=company_number,
        )
        url = reverse(
            'api-v4:ch-company:item',
            kwargs={'company_number': ch_company.company_number},
        )
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'id': ch_company.id,
            'business_type': {
                'id': str(ch_company.business_type.id),
                'name': ch_company.business_type.name,
            },
            'company_number': ch_company.company_number,
            'company_category': ch_company.company_category,
            'company_status': ch_company.company_status,
            'incorporation_date': format_date_or_datetime(ch_company.incorporation_date),
            'name': ch_company.name,
            'registered_address': {
                'line_1': ch_company.registered_address_1 or '',
                'line_2': ch_company.registered_address_2 or '',
                'town': ch_company.registered_address_town or '',
                'county': ch_company.registered_address_county or '',
                'postcode': ch_company.registered_address_postcode or '',
                'country': {
                    'id': str(ch_company.registered_address_country.id),
                    'name': ch_company.registered_address_country.name,
                },
            },
            'sic_code_1': ch_company.sic_code_1,
            'sic_code_2': ch_company.sic_code_2,
            'sic_code_3': ch_company.sic_code_3,
            'sic_code_4': ch_company.sic_code_4,
            'uri': ch_company.uri,
        }

    @pytest.mark.parametrize('verb', ('post', 'patch', 'put'))
    def test_ch_collection_cannot_be_written(self, verb):
        """Test verbs not allowed on CH company collection endpoint."""
        url = reverse('api-v4:ch-company:collection')
        response = getattr(self.api_client, verb)(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize('verb', ('post', 'patch', 'put', 'delete'))
    def test_ch_item_cannot_be_written(self, verb):
        """Test verbs not allowed on CH company item endpoint."""
        ch_company = CompaniesHouseCompanyFactory()
        url = reverse(
            'api-v4:ch-company:item',
            kwargs={'company_number': ch_company.company_number},
        )
        response = getattr(self.api_client, verb)(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
