import pytest
from dateutil.parser import parse as dateutil_parse
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.models import CompaniesHouseCompany as DBCompaniesHouseCompany
from datahub.company.test.factories import CompaniesHouseCompanyFactory
from datahub.core.test_utils import APITestMixin, create_test_user
from datahub.metadata.test.factories import TeamFactory
from datahub.search.companieshousecompany.models import (
    CompaniesHouseCompany as ESCompaniesHouseCompany
)
from datahub.search.signals import sync_es

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
    )

    for company in companies:
        sync_es(ESCompaniesHouseCompany, DBCompaniesHouseCompany, company.pk)

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
                {'111', '222', '333'}
            ),
            (  # pagination
                {
                    'limit': 1,
                    'offset': 1
                },
                {'222'}
            ),
            (  # company number filter
                {
                    'company_number': '222'
                },
                {'222'},
            ),
            (  # incorporation date filter
                {
                    'incorporation_date_after': '2014'
                },
                {'222', '333'},
            ),
            (  # incorporation date filter
                {
                    'incorporation_date_before': '2014'
                },
                {'111'},
            ),
            (  # incorporation date filter
                {
                    'incorporation_date_after': '2014',
                    'incorporation_date_before': '2017'
                },
                {'222', '333'},
            ),
            (  # incorporation date filter
                {
                    'incorporation_date_after': '2010',
                    'incorporation_date_before': '2015-10-01'
                },
                {'111', '222'},
            ),
            (  # company status filter
                {
                    'company_status': ['purring', 'sleeping'],
                },
                {'222', '333'},
            ),
            (  # company name filter
                {
                    'name': 'pallas',
                },
                {'111'},
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
        )
    )
    def test_search(self, setup_data, data, results):
        """Test search results."""
        url = reverse('api-v3:search:companieshousecompany')

        response = self.api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()['results']) == len(results)
        assert {
            item['company_number'] for item in response.json()['results']
        } == results

    def test_incorrect_date_raise_validation_error(self, setup_data):
        """Test that if the date is not in a valid format, the API return a validation error."""
        url = reverse('api-v3:search:companieshousecompany')

        response = self.api_client.post(url, {
            'incorporation_date_after': 'invalid',
            'incorporation_date_before': 'invalid',
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'incorporation_date_after': ['Date is in incorrect format.'],
            'incorporation_date_before': ['Date is in incorrect format.']
        }
