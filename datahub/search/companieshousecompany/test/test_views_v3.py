import pytest
from dateutil.parser import parse as dateutil_parse
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import CompaniesHouseCompanyFactory
from datahub.core.test_utils import APITestMixin, create_test_user
from datahub.metadata.test.factories import TeamFactory
from datahub.search.companieshousecompany import CompaniesHouseCompanySearchApp
from datahub.search.sync_object import sync_object

pytestmark = pytest.mark.django_db


@pytest.fixture
def setup_data(es_with_signals):
    """Sets up data for the tests."""
    companies = (
        CompaniesHouseCompanyFactory(
            name='Pallas',
            company_number='111',
            incorporation_date=dateutil_parse('2012-09-12T00:00:00Z'),
            registered_address_postcode='SW1A 1AA',
            company_status='jumping',
        ),
        CompaniesHouseCompanyFactory(
            name='Jaguarundi',
            company_number='222',
            incorporation_date=dateutil_parse('2015-09-12T00:00:00Z'),
            registered_address_postcode='E1 6JE',
            company_status='sleeping',
        ),
        CompaniesHouseCompanyFactory(
            name='Cheetah',
            company_number='333',
            incorporation_date=dateutil_parse('2016-09-12T00:00:00Z'),
            registered_address_postcode='SW1A 0PW',
            company_status='purring',
        ),
        CompaniesHouseCompanyFactory(
            name='Pallas Second',
            company_number='444',
            incorporation_date=dateutil_parse('2019-09-12T00:00:00Z'),
            registered_address_postcode='WC1B 3DG',
            company_status='crying',
        ),
    )

    for company in companies:
        sync_object(CompaniesHouseCompanySearchApp, company.pk)

    es_with_signals.indices.refresh()


class TestSearchCompaniesHouseCompany(APITestMixin):
    """Test specific search for companies house companies."""

    def test_no_permissions(self):
        """Should return 403"""
        user = create_test_user(dit_team=TeamFactory())
        api_client = self.create_api_client(user=user)
        url = reverse('api-v3:search:companieshousecompany')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize(
        'post_data,expected_results',
        (
            (  # no filter => return all records
                {},
                {'111', '222', '333', '444'},
            ),
            (  # pagination
                {
                    'limit': 1,
                    'offset': 1,
                    'original_query': 'Pallas',
                },
                # exact match should come first, and we're offsetting by 1
                {'444'},
            ),
            (  # original query match
                {
                    'original_query': '111',
                },
                {'111'},
            ),
            (  # original query partial match
                {
                    'original_query': 'jaguar',
                },
                {'222'},
            ),
            (  # original query partial postcode
                {
                    'original_query': 'SW1',
                },
                {'111', '333'},
            ),
        ),
    )
    def test_search(self, setup_data, post_data, expected_results):
        """Test search results."""
        url = reverse('api-v3:search:companieshousecompany')

        response = self.api_client.post(url, post_data)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        actual_results = {
            item['company_number']
            for item in response_data['results']
        }
        assert len(response_data['results']) == len(expected_results)
        assert actual_results == expected_results

    def test_response_body(self, es_with_signals):
        """Tests the response body of a search query."""
        company = CompaniesHouseCompanyFactory(
            name='Pallas',
            company_number='111',
            incorporation_date=dateutil_parse('2012-09-12T00:00:00Z'),
            company_status='jumping',
        )
        sync_object(CompaniesHouseCompanySearchApp, company.pk)
        es_with_signals.indices.refresh()

        url = reverse('api-v3:search:companieshousecompany')
        response = self.api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'count': 1,
            'results': [
                {
                    'id': str(company.pk),
                    'name': company.name,
                    'company_category': company.company_category,
                    'incorporation_date': company.incorporation_date.date().isoformat(),
                    'company_number': company.company_number,
                    'company_status': company.company_status,
                    'registered_address_1': company.registered_address_1,
                    'registered_address_2': company.registered_address_2,
                    'registered_address_town': company.registered_address_town,
                    'registered_address_county': company.registered_address_county,
                    'registered_address_postcode': company.registered_address_postcode,
                    'registered_address_country': {
                        'id': str(company.registered_address_country.id),
                        'name': company.registered_address_country.name,
                    },
                    'sic_code_1': company.sic_code_1,
                    'sic_code_2': company.sic_code_2,
                    'sic_code_3': company.sic_code_3,
                    'sic_code_4': company.sic_code_4,
                    'uri': company.uri,
                },
            ],
        }
