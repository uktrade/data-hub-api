import datetime
from unittest import mock

import pytest
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.reverse import reverse

from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory
from datahub.core import constants
from datahub.core.test_utils import APITestMixin
from datahub.investment.test.factories import InvestmentProjectFactory
from ..views import PaginatedAPIMixin

pytestmark = pytest.mark.django_db


@pytest.fixture
def setup_data():
    """Sets up the data and makes the ES client available."""
    ContactFactory(first_name='abc', last_name='defg')
    ContactFactory(first_name='first', last_name='last')
    InvestmentProjectFactory(
        name='abc defg',
        description='investmentproject1',
        estimated_land_date=datetime.datetime(2011, 6, 13, 9, 44, 31, 62870)
    )
    InvestmentProjectFactory(
        description='investmentproject2',
        estimated_land_date=datetime.datetime(2057, 6, 13, 9, 44, 31, 62870),
        project_manager=AdviserFactory(),
        project_assurance_adviser=AdviserFactory(),
    )

    country_uk = constants.Country.united_kingdom.value.id
    country_us = constants.Country.united_states.value.id
    CompanyFactory(
        name='abc defg ltd',
        trading_address_1='1 Fake Lane',
        trading_address_town='Downtown',
        trading_address_country_id=country_uk
    )
    CompanyFactory(
        name='abc defg us ltd',
        trading_address_1='1 Fake Lane',
        trading_address_town='Downtown',
        trading_address_country_id=country_us,
        registered_address_country_id=country_us
    )


class TestSearch(APITestMixin):
    """Tests search views."""

    def test_basic_search_paging(self, setup_es, setup_data):
        """Tests pagination of results."""
        setup_es.indices.refresh()

        term = 'abc defg'

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(url, {
            'term': term,
            'entity': 'company',
            'offset': 1,
            'limit': 1,
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        assert len(response.data['companies']) == 1

    def test_invalid_entity(self, setup_es, setup_data):
        """Tests case where provided entity is invalid."""
        setup_es.indices.refresh()

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(url, {
            'term': 'test',
            'entity': 'sloths',
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_search_results_quality(self, setup_es, setup_data):
        """Tests quality of results."""
        CompanyFactory(name='The Risk Advisory Group')
        CompanyFactory(name='The Advisory Group')
        CompanyFactory(name='The Advisory')
        CompanyFactory(name='The Advisories')

        setup_es.indices.refresh()

        term = 'The Advisory'

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(url, {
            'term': term,
            'entity': 'company'
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 4

        # results are in order of relevance if sortby is not applied
        assert [
            'The Advisory',
            'The Advisory Group',
            'The Risk Advisory Group',
            'The Advisories'
        ] == [company['name'] for company in response.data['companies']]

    def test_search_partial_match(self, setup_es, setup_data):
        """Tests partial matching."""
        CompanyFactory(name='Veryuniquename1')
        CompanyFactory(name='Veryuniquename2')
        CompanyFactory(name='Veryuniquename3')
        CompanyFactory(name='Veryuniquename4')

        setup_es.indices.refresh()

        term = 'Veryuniquenam'

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(url, {
            'term': term,
            'entity': 'company'
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 4

        # particular order is not important here, we just need all that partially match
        assert {
            'Veryuniquename1',
            'Veryuniquename2',
            'Veryuniquename3',
            'Veryuniquename4'
        } == {company['name'] for company in response.data['companies']}

    def test_search_hyphen_match(self, setup_es, setup_data):
        """Tests hyphen query."""
        CompanyFactory(name='t-shirt')
        CompanyFactory(name='tshirt')
        CompanyFactory(name='electronic shirt')
        CompanyFactory(name='t and e and a')

        setup_es.indices.refresh()

        term = 't-shirt'

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(url, {
            'term': term,
            'entity': 'company'
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 4

        # order of relevance
        assert [
            't-shirt',
            'tshirt',
            'electronic shirt',
            't and e and a'
        ] == [company['name'] for company in response.data['companies']]

    def test_search_id_match(self, setup_es, setup_data):
        """Tests exact id matching."""
        CompanyFactory(id='0fb3379c-341c-4dc4-b125-bf8d47b26baa')
        CompanyFactory(id='0fb2379c-341c-4dc4-b225-bf8d47b26baa')
        CompanyFactory(id='0fb4379c-341c-4dc4-b325-bf8d47b26baa')
        CompanyFactory(id='0fb5379c-341c-4dc4-b425-bf8d47b26baa')

        setup_es.indices.refresh()

        term = '0fb4379c-341c-4dc4-b325-bf8d47b26baa'

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(url, {
            'term': term,
            'entity': 'company'
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert '0fb4379c-341c-4dc4-b325-bf8d47b26baa' == response.data['companies'][0]['id']

    def test_search_sort_desc(self, setup_es, setup_data):
        """Tests sorting in descending order."""
        CompanyFactory(name='Water 1')
        CompanyFactory(name='water 2')
        CompanyFactory(name='water 3')
        CompanyFactory(name='Water 4')

        setup_es.indices.refresh()

        term = 'Water'

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(url, {
            'term': term,
            'sortby': 'name:desc',
            'entity': 'company'
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 4
        assert ['Water 4',
                'water 3',
                'water 2',
                'Water 1'] == [company['name'] for company in response.data['companies']]

    def test_search_sort_asc(self, setup_es, setup_data):
        """Tests sorting in ascending order."""
        CompanyFactory(name='Fire 4')
        CompanyFactory(name='fire 3')
        CompanyFactory(name='fire 2')
        CompanyFactory(name='Fire 1')

        setup_es.indices.refresh()

        term = 'Fire'

        url = reverse('api-v3:search:company')
        response = self.api_client.post(url, {
            'original_query': term,
            'sortby': 'name:asc'
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 4
        assert ['Fire 1',
                'fire 2',
                'fire 3',
                'Fire 4'] == [company['name'] for company in response.data['results']]

    def test_search_sort_nested_desc(self, setup_es, setup_data):
        """Tests sorting by nested field."""
        InvestmentProjectFactory(
            name='Potato 1',
            stage_id=constants.InvestmentProjectStage.active.value.id,
        )
        InvestmentProjectFactory(
            name='Potato 2',
            stage_id=constants.InvestmentProjectStage.prospect.value.id,
        )
        InvestmentProjectFactory(
            name='potato 3',
            stage_id=constants.InvestmentProjectStage.won.value.id,
        )
        InvestmentProjectFactory(
            name='Potato 4',
            stage_id=constants.InvestmentProjectStage.won.value.id,
        )

        setup_es.indices.refresh()

        term = 'Potato'

        url = reverse('api-v3:search:investment_project')
        response = self.api_client.post(url, {
            'original_query': term,
            'sortby': 'stage.name:desc',
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 4
        assert ['Won',
                'Won',
                'Prospect',
                'Active'] == [investment_project['stage']['name']
                              for investment_project in response.data['results']]

    def test_search_sort_invalid(self, setup_es, setup_data):
        """Tests attempt to sort by non existent field."""
        CompanyFactory(name='Fire 4')
        CompanyFactory(name='fire 3')
        CompanyFactory(name='fire 2')
        CompanyFactory(name='Fire 1')

        setup_es.indices.refresh()

        term = 'Fire'

        url = reverse('api-v3:search:company')
        response = self.api_client.post(url, {
            'original_query': term,
            'sortby': 'some_field_that_doesnt_exist:asc'
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_search_sort_asc_with_null_values(self, setup_es, setup_data):
        """Tests placement of null values in sorted results when order is ascending."""
        InvestmentProjectFactory(name='Earth 1', total_investment=1000)
        InvestmentProjectFactory(name='Earth 2')

        setup_es.indices.refresh()

        term = 'Earth'

        url = reverse('api-v3:search:investment_project')
        response = self.api_client.post(url, {
            'original_query': term,
            'sortby': 'total_investment:asc'
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        assert [('Earth 2', None),
                ('Earth 1', 1000)] == [(investment['name'], investment['total_investment'],)
                                       for investment in response.data['results']]

    def test_search_sort_desc_with_null_values(self, setup_es, setup_data):
        """Tests placement of null values in sorted results when order is descending."""
        InvestmentProjectFactory(name='Ether 1', total_investment=1000)
        InvestmentProjectFactory(name='Ether 2')

        setup_es.indices.refresh()

        term = 'Ether'

        url = reverse('api-v3:search:investment_project')
        response = self.api_client.post(url, {
            'original_query': term,
            'sortby': 'total_investment:desc'
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        assert [('Ether 1', 1000),
                ('Ether 2', None)] == [(investment['name'], investment['total_investment'],)
                                       for investment in response.data['results']]

    def test_search_contact_by_country_case_insensitive(self, setup_es, setup_data):
        """Tests detailed contact search."""
        ContactFactory(
            first_name='John',
            last_name='Doe',
            address_same_as_company=False,
            address_1='Happy Lane',
            address_town='Happy Town',
            address_country_id=constants.Country.united_states.value.id,
        )

        setup_es.indices.refresh()

        term = 'united states'

        url = reverse('api-v3:search:basic')

        response = self.api_client.get(url, {
            'term': term,
            'entity': 'contact',
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert len(response.data['contacts']) == 1
        assert response.data['contacts'][0]['address_country']['name'] == 'United States'

    def test_basic_search_aggregations(self, setup_es, setup_data):
        """Tests basic aggregate query."""
        company = CompanyFactory(name='very_unique_company')
        ContactFactory(company=company)
        InvestmentProjectFactory(investor_company=company)

        setup_es.indices.refresh()

        term = 'very_unique_company'

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(url, {
            'term': term,
            'entity': 'company'
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['companies'][0]['name'] == 'very_unique_company'

        aggregations = [{'count': 1, 'entity': 'company'},
                        {'count': 1, 'entity': 'contact'},
                        {'count': 1, 'entity': 'investment_project'}]
        assert all(aggregation in response.data['aggregations'] for aggregation in aggregations)


class TestPaginatedAPIMixin:
    """Tests related to the paginated API mixin."""

    def test_limit_as_valid_param(self):
        """Test that get_limit returns the int value of the param if valid."""
        mixin = PaginatedAPIMixin()

        request = mock.MagicMock(
            data={
                PaginatedAPIMixin.limit_query_param: '3'
            }
        )

        assert mixin.get_limit(request) == 3

    def test_limit_as_non_int_defaults(self):
        """Test that get_limit returns the default value if the param is not an int."""
        mixin = PaginatedAPIMixin()

        request = mock.MagicMock(
            data={
                PaginatedAPIMixin.limit_query_param: 'non-int'
            }
        )

        assert mixin.get_limit(request) == PaginatedAPIMixin.default_limit

    def test_limit_as_negative_int_defaults(self):
        """Test that get_limit returns the default value if param is a negative value."""
        mixin = PaginatedAPIMixin()

        request = mock.MagicMock(
            data={
                PaginatedAPIMixin.limit_query_param: '-1'
            }
        )

        assert mixin.get_limit(request) == PaginatedAPIMixin.default_limit

    def test_limit_as_zero_defaults(self):
        """Test that get_limit returns the default value if param is 0."""
        mixin = PaginatedAPIMixin()

        request = mock.MagicMock(
            data={
                PaginatedAPIMixin.limit_query_param: '0'
            }
        )

        assert mixin.get_limit(request) == PaginatedAPIMixin.default_limit

    def test_offset_as_valid_param(self):
        """Test that get_offset returns the int value if the param is valid."""
        mixin = PaginatedAPIMixin()

        request = mock.MagicMock(
            data={
                PaginatedAPIMixin.offset_query_param: '4'
            }
        )

        assert mixin.get_offset(request) == 4

    def test_offset_as_non_int_defaults(self):
        """Test that get_offset returns the default value if the param is not an int."""
        mixin = PaginatedAPIMixin()

        request = mock.MagicMock(
            data={
                PaginatedAPIMixin.offset_query_param: 'non-int'
            }
        )

        assert mixin.get_offset(request) == 0

    def test_pagination_params_within_limit(self):
        """Test that if the result window (offset + limit) is within limit, everything is OK."""
        mixin = PaginatedAPIMixin()

        request = mock.MagicMock(
            data={
                PaginatedAPIMixin.limit_query_param: '100',
                PaginatedAPIMixin.offset_query_param: '9900',
            }
        )

        limit, offset = mixin.get_pagination_values(request)

        assert limit == 100
        assert offset == 9900

    def test_pagination_params_outside_limit(self):
        """
        Test that if the result window (offset + limit) is too large,
        a validator error is returned.
        """
        mixin = PaginatedAPIMixin()

        request = mock.MagicMock(
            data={
                PaginatedAPIMixin.limit_query_param: '100',
                PaginatedAPIMixin.offset_query_param: '9901',
            }
        )

        with pytest.raises(ValidationError):
            mixin.get_pagination_values(request)
