from cgi import parse_header
from csv import DictReader
from io import StringIO
from unittest import mock

import pytest
from django.conf import settings
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.models import Company, CompanyPermission
from datahub.company.test.factories import (
    CompanyFactory,
)
from datahub.core import constants
from datahub.core.constants import Country
from datahub.core.exceptions import DataHubException
from datahub.core.test_utils import (
    APITestMixin,
    create_test_user,
    format_csv_data,
    get_attr_or_none,
)
from datahub.metadata.test.factories import TeamFactory
from datahub.search.company.views import SearchCompanyExportAPIView

pytestmark = pytest.mark.django_db


@pytest.fixture
def setup_data(setup_es):
    """Sets up data for the tests."""
    country_uk = constants.Country.united_kingdom.value.id
    country_us = constants.Country.united_states.value.id
    uk_region = constants.UKRegion.south_east.value.id
    CompanyFactory(
        name='abc defg ltd',
        trading_names=['helm', 'nop'],
        address_1='1 Fake Lane',
        address_town='Downtown',
        address_country_id=country_uk,
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
    setup_es.indices.refresh()


@pytest.fixture
def setup_headquarters_data(setup_es):
    """Sets up data for headquarter type tests."""
    CompanyFactory(
        name='ghq',
        headquarter_type_id=constants.HeadquarterType.ghq.value.id,
    )
    CompanyFactory(
        name='ehq',
        headquarter_type_id=constants.HeadquarterType.ehq.value.id,
    )
    CompanyFactory(
        name='ukhq',
        headquarter_type_id=constants.HeadquarterType.ukhq.value.id,
    )
    CompanyFactory(
        name='none',
        headquarter_type_id=None,
    )
    setup_es.indices.refresh()


class TestCompanyExportView(APITestMixin):
    """Tests the company export view."""

    @pytest.mark.parametrize(
        'permissions',
        (
            (),
            (CompanyPermission.view_company,),
            (CompanyPermission.export_company,),
        ),
    )
    def test_user_without_permission_cannot_export(self, setup_es, permissions):
        """Test that a user without the correct permissions cannot export data."""
        user = create_test_user(dit_team=TeamFactory(), permission_codenames=permissions)
        api_client = self.create_api_client(user=user)

        url = reverse('api-v3:search:company-export')
        response = api_client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize(
        'request_sortby,orm_ordering',
        (
            ('name', 'name'),
            ('modified_on', 'modified_on'),
            ('modified_on:desc', '-modified_on'),
        ),
    )
    def test_export(
        self,
        setup_es,
        request_sortby,
        orm_ordering,
    ):
        """Test export of company search results."""
        CompanyFactory.create_batch(
            3,
            turnover=None,
            is_turnover_estimated=None,
            number_of_employees=None,
            is_number_of_employees_estimated=None,
        )
        CompanyFactory.create_batch(
            2,
            hq=True,
            turnover=100,
            is_turnover_estimated=True,
            number_of_employees=95,
            is_number_of_employees_estimated=True,
        )

        setup_es.indices.refresh()

        data = {}
        if request_sortby:
            data['sortby'] = request_sortby

        url = reverse('api-v3:search:company-export')

        with freeze_time('2018-01-01 11:12:13'):
            response = self.api_client.post(url, data=data)

        assert response.status_code == status.HTTP_200_OK
        assert parse_header(response.get('Content-Type')) == ('text/csv', {'charset': 'utf-8'})
        assert parse_header(response.get('Content-Disposition')) == (
            'attachment', {'filename': 'Data Hub - Companies - 2018-01-01-11-12-13.csv'},
        )

        sorted_company = Company.objects.order_by(orm_ordering, 'pk')
        reader = DictReader(StringIO(response.getvalue().decode('utf-8-sig')))

        assert reader.fieldnames == list(SearchCompanyExportAPIView.field_titles.values())

        expected_row_data = [
            {
                'Name': company.name,
                'Link': f'{settings.DATAHUB_FRONTEND_URL_PREFIXES["company"]}/{company.pk}',
                'Sector': get_attr_or_none(company, 'sector.name'),
                'Country': get_attr_or_none(company, 'address_country.name'),
                'UK region': get_attr_or_none(company, 'uk_region.name'),
                'Archived': company.archived,
                'Date created': company.created_on,
                'Number of employees': (
                    company.number_of_employees
                    if company.number_of_employees is not None
                    else get_attr_or_none(company, 'employee_range.name')
                ),
                'Annual turnover': (
                    f'${company.turnover}'
                    if company.turnover is not None
                    else get_attr_or_none(company, 'turnover_range.name')
                ),
                'Headquarter type':
                    (get_attr_or_none(company, 'headquarter_type.name') or '').upper(),
            }
            for company in sorted_company
        ]

        assert list(dict(row) for row in reader) == format_csv_data(expected_row_data)


class TestAutocompleteSearch(APITestMixin):
    """Tests for autocomplete search views."""

    def test_no_permissions_returns_403(self):
        """Should return 403"""
        user = create_test_user(dit_team=TeamFactory())
        api_client = self.create_api_client(user=user)
        url = reverse('api-v3:search:company-autocomplete')

        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_response_body(self, setup_es):
        """Tests the response body of autocomplete search query."""
        company = CompanyFactory(
            name='abc',
            trading_names=['Xyz trading', 'Abc trading'],
        )
        setup_es.indices.refresh()

        url = reverse('api-v3:search:company-autocomplete')
        response = self.api_client.get(url, data={'term': 'abc'})

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'count': 1,
            'results': [
                {
                    'id': str(company.id),
                    'name': company.name,
                    'trading_address_1': company.trading_address_1,
                    'trading_address_2': company.trading_address_2,
                    'trading_address_county': company.trading_address_county,
                    'trading_address_postcode': company.trading_address_postcode,
                    'trading_address_town': company.trading_address_town,
                    'trading_address_country': {
                        'id': str(company.trading_address_country.id),
                        'name': company.trading_address_country.name,
                    },
                    'registered_address_1': company.registered_address_1,
                    'registered_address_2': company.registered_address_2,
                    'registered_address_town': company.registered_address_town,
                    'registered_address_county': company.registered_address_county,
                    'registered_address_postcode': company.registered_address_postcode,
                    'registered_address_country': {
                        'id': str(Country.united_kingdom.value.id),
                        'name': Country.united_kingdom.value.name,
                    },
                    'trading_names': ['Xyz trading', 'Abc trading'],
                },
            ],
        }

    @pytest.mark.parametrize(
        'data,expected_error',
        (
            (
                {},
                {'term': ['This field is required.']},
            ),
            (
                {'term': 'a', 'limit': 0},
                {'limit': ['Ensure this value is greater than or equal to 1.']},
            ),
            (
                {'term': 'a', 'limit': 'asdf'},
                {'limit': ['A valid integer is required.']},
            ),
        ),
    )
    def test_validation_error(self, data, expected_error, setup_data):
        """Tests case where there is not query provided."""
        url = reverse('api-v3:search:company-autocomplete')

        response = self.api_client.get(url, data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == expected_error

    @pytest.mark.parametrize(
        'query,expected_companies',
        (
            ('abc', ['abc defg ltd', 'abc defg us ltd']),
            ('abv', []),
            ('ABC', ['abc defg ltd', 'abc defg us ltd']),
            ('hello', []),
            ('', []),
            (1, []),
            ('abc defg ltd', ['abc defg ltd']),
            ('defg', ['abc defg ltd', 'abc defg us ltd']),
            ('us', ['abc defg us ltd']),
            ('hel', ['abc defg ltd', 'abc defg us ltd']),
            ('qrs', ['abc defg us ltd']),
            ('help qrs', []),
        ),
    )
    def test_searching_with_a_query(self, setup_data, query, expected_companies):
        """Tests case where search queries are provided."""
        url = reverse('api-v3:search:company-autocomplete')

        response = self.api_client.get(url, data={'term': query})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == len(expected_companies)

        if expected_companies:
            companies = [result['name'] for result in response.data['results']]
            assert companies == expected_companies

    @pytest.mark.parametrize(
        'limit,expected_companies',
        (
            (10, ['abc defg ltd', 'abc defg us ltd']),  # only 2 found
            (2, ['abc defg ltd', 'abc defg us ltd']),
            (1, ['abc defg ltd']),
        ),
    )
    def test_searching_with_limit(self, setup_data, limit, expected_companies):
        """Tests case where search limit is provided."""
        url = reverse('api-v3:search:company-autocomplete')

        response = self.api_client.get(
            url,
            data={
                'term': 'abc',
                'limit': limit,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == len(expected_companies)

        if expected_companies:
            companies = [result['name'] for result in response.data['results']]
            assert companies == expected_companies

    @mock.patch(
        'datahub.search.company.views.'
        'CompanyAutocompleteSearchListAPIViewV3._get_permission_filters',
    )
    def test_raise_datahub_error_when_search_app_has_permission_search_filters(
        self, mock_get_app_permission_filters,
    ):
        """
        Tests if a search app has permission filters, if so autocomplete is not
        permitted and a datahub exception error is raised.
        """
        mock_get_app_permission_filters.return_value = True
        url = reverse('api-v3:search:company-autocomplete')
        with pytest.raises(DataHubException) as expected_error:
            self.api_client.get(url, data={'term': 'query'})
        assert (
            str(expected_error.value)
            == 'Unable to apply filtering for autocomplete search request'
        )
