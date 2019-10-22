import uuid
from collections import Counter
from uuid import UUID, uuid4

import factory
import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.models import Company
from datahub.company.test.factories import CompanyFactory
from datahub.core import constants
from datahub.core.test_utils import HawkAPITestClient


@pytest.fixture
def setup_data(es_with_collector):
    """Sets up data for the tests."""
    country_uk = constants.Country.united_kingdom.value.id
    country_us = constants.Country.united_states.value.id
    country_anguilla = constants.Country.anguilla.value.id
    uk_region = constants.UKRegion.south_east.value.id
    CompanyFactory(
        name='abc defg ltd',
        trading_names=['helm', 'nop'],
        address_1='1 Fake Lane',
        address_town='Downtown',
        address_country_id=country_uk,
        registered_address_country_id=country_uk,
        uk_region_id=uk_region,
    )
    CompanyFactory(
        name='abc defg us ltd',
        trading_names=['helm', 'nop', 'qrs'],
        address_1='1 Fake Lane',
        address_town='Downtown',
        address_country_id=country_us,
        registered_address_country_id=country_us,
    )
    CompanyFactory(
        name='archived',
        trading_names=[],
        address_1='Main Lane',
        address_town='Somewhere',
        address_country_id=country_anguilla,
        registered_address_country_id=country_anguilla,
        archived=True,
    )
    es_with_collector.flush_and_refresh()


@pytest.fixture
def hawk_api_client():
    """Hawk API client fixture."""
    yield HawkAPITestClient()


@pytest.fixture
def public_company_api_client(hawk_api_client):
    """Hawk API client fixture configured to use credentials with the public_company scope."""
    hawk_api_client.set_credentials(
        'public-company-id',
        'public-company-key',
    )
    yield hawk_api_client


@pytest.mark.django_db
class TestPublicCompanySearch:
    """Tests the public company search."""

    def test_without_credentials(self, api_client):
        """Test that making a request without credentials returns an error."""
        url = reverse('api-v4:search:public-company')
        response = api_client.post(url, data={})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_without_scope(self, hawk_api_client):
        """Test that making a request without the correct Hawk scope returns an error."""
        hawk_api_client.set_credentials(
            'test-id-without-scope',
            'test-key-without-scope',
        )
        url = reverse('api-v4:search:public-company')
        response = hawk_api_client.post(url, {})

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_without_whitelisted_ip(self, public_company_api_client):
        """Test that making a request without the whitelisted client IP returns an error."""
        url = reverse('api-v4:search:public-company')
        public_company_api_client.set_http_x_forwarded_for('1.1.1.1')
        response = public_company_api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_response_body(self, es_with_collector, public_company_api_client):
        """Tests the response body of a search query."""
        company = CompanyFactory(
            company_number='123',
            trading_names=['Xyz trading', 'Abc trading'],
            global_headquarters=None,
            one_list_tier=None,
            one_list_account_owner=None,
        )
        es_with_collector.flush_and_refresh()

        url = reverse('api-v4:search:public-company')
        response = public_company_api_client.post(url, {})

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'count': 1,
            'results': [
                {
                    'id': str(company.pk),
                    'created_on': company.created_on.isoformat(),
                    'modified_on': company.modified_on.isoformat(),
                    'name': company.name,
                    'reference_code': company.reference_code,
                    'company_number': company.company_number,
                    'vat_number': company.vat_number,
                    'duns_number': company.duns_number,
                    'trading_names': company.trading_names,
                    'address': {
                        'line_1': company.address_1,
                        'line_2': company.address_2 or '',
                        'town': company.address_town,
                        'county': company.address_county or '',
                        'postcode': company.address_postcode or '',
                        'country': {
                            'id': str(company.address_country.id),
                            'name': company.address_country.name,
                        },
                    },
                    'registered_address': {
                        'line_1': company.registered_address_1,
                        'line_2': company.registered_address_2 or '',
                        'town': company.registered_address_town,
                        'county': company.registered_address_county or '',
                        'postcode': company.registered_address_postcode or '',
                        'country': {
                            'id': str(company.registered_address_country.id),
                            'name': company.registered_address_country.name,
                        },
                    },
                    'uk_based': (
                        company.address_country.id == uuid.UUID(
                            constants.Country.united_kingdom.value.id,
                        )
                    ),
                    'uk_region': {
                        'id': str(company.uk_region.id),
                        'name': company.uk_region.name,
                    },
                    'business_type': {
                        'id': str(company.business_type.id),
                        'name': company.business_type.name,
                    },
                    'description': company.description,
                    'employee_range': {
                        'id': str(company.employee_range.id),
                        'name': company.employee_range.name,
                    },
                    'export_experience_category': {
                        'id': str(company.export_experience_category.id),
                        'name': company.export_experience_category.name,
                    },
                    'export_to_countries': [],
                    'future_interest_countries': [],
                    'headquarter_type': company.headquarter_type,
                    'sector': {
                        'id': str(company.sector.id),
                        'name': company.sector.name,
                        'ancestors': [
                            {'id': str(ancestor.id)}
                            for ancestor in company.sector.get_ancestors()
                        ],
                    },
                    'turnover_range': {
                        'id': str(company.turnover_range.id),
                        'name': company.turnover_range.name,
                    },
                    'website': company.website,
                    'global_headquarters': None,
                    'archived': False,
                    'archived_on': None,
                    'archived_reason': None,
                },
            ],
        }

    def test_response_is_signed(self, es, public_company_api_client):
        """Test that responses are signed."""
        url = reverse('api-v4:search:public-company')
        response = public_company_api_client.post(url, {})

        assert response.status_code == status.HTTP_200_OK
        assert 'Server-Authorization' in response

    @pytest.mark.parametrize(
        'filters,expected_companies',
        (
            # no filter
            (
                {},
                ['abc defg ltd', 'abc defg us ltd', 'archived'],
            ),

            # archived True
            (
                {
                    'archived': True,
                },
                ['archived'],
            ),

            # archived False
            (
                {
                    'archived': False,
                },
                ['abc defg ltd', 'abc defg us ltd'],
            ),
        ),
    )
    def test_filters(self, public_company_api_client, setup_data, filters, expected_companies):
        """Tests different filters."""
        url = reverse('api-v4:search:public-company')
        response = public_company_api_client.post(url, filters)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == len(expected_companies)
        actual_names = [result['name'] for result in response_data['results']]
        assert Counter(actual_names) == Counter(expected_companies)

    @pytest.mark.parametrize(
        'name_term,matched_company_name',
        (
            # name
            ('whiskers', 'whiskers and tabby'),
            ('whi', 'whiskers and tabby'),
            ('his', 'whiskers and tabby'),
            ('ers', 'whiskers and tabby'),
            ('1a', '1a'),

            # trading names
            ('maine coon egyptian mau', 'whiskers and tabby'),
            ('maine', 'whiskers and tabby'),
            ('mau', 'whiskers and tabby'),
            ('ine oon', 'whiskers and tabby'),
            ('ine mau', 'whiskers and tabby'),
            ('3a', '1a'),

            # non-matches
            ('whi lorem', None),
            ('wh', None),
            ('whe', None),
            ('tiger', None),
            ('panda', None),
            ('moine', None),
        ),
    )
    def test_composite_name_filter(
        self,
        public_company_api_client,
        es_with_collector,
        name_term,
        matched_company_name,
    ):
        """Tests composite name filter."""
        CompanyFactory(
            name='whiskers and tabby',
            trading_names=['Maine Coon', 'Egyptian Mau'],
        )
        CompanyFactory(
            name='1a',
            trading_names=['3a', '4a'],
        )
        es_with_collector.flush_and_refresh()

        url = reverse('api-v4:search:public-company')
        request_data = {
            'name': name_term,
        }
        response = public_company_api_client.post(url, request_data)
        assert response.status_code == status.HTTP_200_OK

        match = Company.objects.filter(name=matched_company_name).first()
        if match:
            assert response.data['count'] == 1
            assert len(response.data['results']) == 1
            assert response.data['results'][0]['id'] == str(match.id)
        else:
            assert response.data['count'] == 0
            assert len(response.data['results']) == 0

    def test_pagination(self, public_company_api_client, es_with_collector):
        """Test result pagination."""
        total_records = 9
        page_size = 2
        ids = sorted((uuid4() for _ in range(total_records)))
        name = 'test record'

        CompanyFactory.create_batch(
            len(ids),
            id=factory.Iterator(ids),
            name=name,
            trading_names=[],
        )

        es_with_collector.flush_and_refresh()

        url = reverse('api-v4:search:public-company')

        num_pages = (total_records + page_size - 1) // page_size
        for page in range(num_pages):
            request_data = {
                'original_query': name,
                'offset': page * page_size,
                'limit': page_size,
            }
            response = public_company_api_client.post(url, request_data)
            assert response.status_code == status.HTTP_200_OK

            start = page * page_size
            end = start + page_size
            assert [
                UUID(company['id']) for company in response.data['results']
            ] == ids[start:end]
