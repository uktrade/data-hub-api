import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.models import Company
from datahub.company.test.factories import CompanyFactory
from datahub.core import constants
from datahub.core.test_utils import APITestMixin

pytestmark = pytest.mark.django_db


@pytest.fixture
def setup_data(es_with_signals):
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
    es_with_signals.indices.refresh()


class TestBasicSearch(APITestMixin):
    """Tests basic search view."""

    def test_all_companies(self, setup_data):
        """Tests basic aggregate all companies query."""
        url = reverse('api-v3:search:basic')
        response = self.api_client.get(
            url,
            data={
                'term': '',
                'entity': 'company',
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] > 0

    def test_companies(self, setup_data):
        """Tests basic aggregate companies query."""
        term = 'abc defg'

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(
            url,
            data={
                'term': term,
                'entity': 'company',
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        assert response.data['results'][0]['name'].startswith(term)
        assert [{'count': 2, 'entity': 'company'}] == response.data['aggregations']

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
    def test_search_in_name(self, es_with_signals, name_term, matched_company_name):
        """Tests basic aggregate companies query."""
        CompanyFactory(
            name='whiskers and tabby',
            trading_names=['Maine Coon', 'Egyptian Mau'],
        )
        CompanyFactory(
            name='1a',
            trading_names=['3a', '4a'],
        )
        es_with_signals.indices.refresh()

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(
            url,
            data={
                'term': name_term,
                'entity': 'company',
            },
        )

        match = Company.objects.filter(name=matched_company_name).first()
        if match:
            assert response.data['count'] == 1
            assert len(response.data['results']) == 1
            assert response.data['results'][0]['id'] == str(match.id)
            assert [{'count': 1, 'entity': 'company'}] == response.data['aggregations']
        else:
            assert response.data['count'] == 0
            assert len(response.data['results']) == 0

    @pytest.mark.parametrize(
        'model_field,model_value,search_term,match_found',
        (
            ('address_postcode', 'SW1A 1AA', 'SW1A 1AA', True),
            ('address_postcode', 'SW1A 1AA', 'SW1A 1AB', False),
            ('registered_address_postcode', 'SW1A 1AA', 'SW1A 1AA', True),
            ('registered_address_postcode', 'SW1A 1AA', 'SW1A 1AB', False),
        ),
    )
    def test_search_in_field(
        self,
        es_with_signals,
        model_field,
        model_value,
        search_term,
        match_found,
    ):
        """Tests basic aggregate companies query."""
        CompanyFactory()
        CompanyFactory(
            **{
                'name': 'test_company',
                model_field: model_value,
            },
        )
        es_with_signals.indices.refresh()

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(
            url,
            data={
                'term': search_term,
                'entity': 'company',
            },
        )

        assert response.status_code == status.HTTP_200_OK
        if match_found:
            assert response.data['count'] == 1
            assert response.data['results'][0]['name'] == 'test_company'
        else:
            assert response.data['count'] == 0

    def test_no_results(self, setup_data):
        """Tests case where there should be no results."""
        term = 'there-should-be-no-match'

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(
            url,
            data={
                'term': term,
                'entity': 'company',
            },
        )

        assert response.data['count'] == 0

    def test_companies_no_term(self, setup_data):
        """Tests case where there is not term provided."""
        url = reverse('api-v3:search:basic')
        response = self.api_client.get(url, {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
