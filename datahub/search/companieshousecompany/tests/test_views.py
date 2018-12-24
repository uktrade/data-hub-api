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
def setup_data(setup_es):
    """Sets up data for the tests."""
    companies = (
        CompaniesHouseCompanyFactory(
            name='Pallas',
            company_number='111',
            incorporation_date=dateutil_parse('2012-09-12T00:00:00Z'),
            company_status='jumping',
        ),
        CompaniesHouseCompanyFactory(
            name='Jaguarundi',
            company_number='222',
            incorporation_date=dateutil_parse('2015-09-12T00:00:00Z'),
            company_status='sleeping',
        ),
        CompaniesHouseCompanyFactory(
            name='Cheetah',
            company_number='333',
            incorporation_date=dateutil_parse('2016-09-12T00:00:00Z'),
            company_status='purring',
        ),
        CompaniesHouseCompanyFactory(
            name='Pallas Second',
            company_number='444',
            incorporation_date=dateutil_parse('2019-09-12T00:00:00Z'),
            company_status='crying',
        ),
    )

    for company in companies:
        sync_object(CompaniesHouseCompanySearchApp, company.pk)

    setup_es.indices.refresh()


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
        'data,results',
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
        ),
    )
    def test_search(self, setup_data, data, results):
        """Test search results."""
        url = reverse('api-v3:search:companieshousecompany')

        response = self.api_client.post(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()['results']) == len(results)
        assert {
            item['company_number'] for item in response.json()['results']
        } == results
