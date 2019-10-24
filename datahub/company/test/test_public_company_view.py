import uuid

import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.models import OneListTier
from datahub.company.test.factories import AdviserFactory, CompanyFactory
from datahub.core.constants import Country
from datahub.core.test_utils import format_date_or_datetime, HawkAPITestClient


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
class TestPublicCompanyViewSet:
    """Tests for the Hawk-authenticated public company view."""

    def test_without_credentials(self, api_client):
        """Test that making a request without credentials returns an error."""
        company = CompanyFactory()

        url = reverse('api-v4:company:public-item', kwargs={'pk': company.pk})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_without_scope(self, hawk_api_client):
        """Test that making a request without the correct Hawk scope returns an error."""
        company = CompanyFactory()
        hawk_api_client.set_credentials(
            'test-id-without-scope',
            'test-key-without-scope',
        )
        url = reverse('api-v4:company:public-item', kwargs={'pk': company.pk})
        response = hawk_api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_without_whitelisted_ip(self, public_company_api_client):
        """Test that making a request without the whitelisted IP returns an error."""
        company = CompanyFactory()
        url = reverse('api-v4:company:public-item', kwargs={'pk': company.pk})
        public_company_api_client.set_http_x_forwarded_for('1.1.1.1')
        response = public_company_api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize('method', ('delete', 'patch', 'post', 'put'))
    def test_other_methods_not_allowed(self, method, public_company_api_client):
        """Test that various HTTP methods are not allowed."""
        company = CompanyFactory()

        url = reverse('api-v4:company:public-item', kwargs={'pk': company.pk})
        response = public_company_api_client.request(method, url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_response_is_signed(self, es_with_signals, public_company_api_client):
        """Test that responses are signed."""
        company = CompanyFactory()
        url = reverse('api-v4:company:public-item', kwargs={'pk': company.pk})
        response = public_company_api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert 'Server-Authorization' in response

    def test_get(self, public_company_api_client):
        """Test getting a single company."""
        ghq = CompanyFactory(
            global_headquarters=None,
            one_list_tier=OneListTier.objects.first(),
            one_list_account_owner=AdviserFactory(),
        )
        company = CompanyFactory(
            company_number='123',
            trading_names=['Xyz trading', 'Abc trading'],
            global_headquarters=ghq,
            one_list_tier=None,
            one_list_account_owner=None,
        )

        url = reverse('api-v4:company:public-item', kwargs={'pk': company.id})
        response = public_company_api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
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
            'archived': False,
            'archived_on': None,
            'archived_reason': None,
            'business_type': {
                'id': str(company.business_type.id),
                'name': company.business_type.name,
            },
            'company_number': company.company_number,
            'created_on': format_date_or_datetime(company.created_on),
            'description': company.description,
            'duns_number': company.duns_number,
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
            'global_headquarters': {
                'id': str(ghq.id),
                'name': ghq.name,
            },
            'headquarter_type': company.headquarter_type,
            'id': str(company.pk),
            'is_number_of_employees_estimated': company.is_number_of_employees_estimated,
            'is_turnover_estimated': company.is_turnover_estimated,
            'modified_on': format_date_or_datetime(company.modified_on),
            'name': company.name,
            'number_of_employees': company.number_of_employees,
            'one_list_group_tier': {
                'id': str(ghq.one_list_tier.id),
                'name': ghq.one_list_tier.name,
            },
            'reference_code': company.reference_code,
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
            'sector': {
                'id': str(company.sector.id),
                'name': company.sector.name,
            },
            'trading_names': company.trading_names,
            'vat_number': company.vat_number,
            'uk_based': (
                company.address_country.id == uuid.UUID(Country.united_kingdom.value.id)
            ),
            'uk_region': {
                'id': str(company.uk_region.id),
                'name': company.uk_region.name,
            },
            'transferred_on': None,
            'transferred_to': None,
            'transfer_reason': '',
            'turnover_range': {
                'id': str(company.turnover_range.id),
                'name': company.turnover_range.name,
            },
            'turnover': company.turnover,
            'website': company.website,
        }

    def test_get_company_without_country(self, public_company_api_client):
        """
        Tests the company item view for a company without a country.

        Checks that the endpoint returns 200 and the uk_based attribute is
        set to None.
        """
        company = CompanyFactory(
            address_country_id=None,
        )

        url = reverse('api-v4:company:public-item', kwargs={'pk': company.id})
        response = public_company_api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['uk_based'] is None

    @pytest.mark.parametrize(
        'input_website,expected_website',
        (
            ('www.google.com', 'http://www.google.com'),
            ('http://www.google.com', 'http://www.google.com'),
            ('https://www.google.com', 'https://www.google.com'),
            ('', ''),
            (None, None),
        ),
    )
    def test_get_company_with_website(
        self,
        input_website,
        expected_website,
        public_company_api_client,
    ):
        """
        Test that if the website field on a company doesn't have any scheme
        specified, the endpoint adds it automatically.
        """
        company = CompanyFactory(
            website=input_website,
        )
        url = reverse('api-v4:company:public-item', kwargs={'pk': company.pk})
        response = public_company_api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['website'] == expected_website

    @pytest.mark.parametrize(
        'build_company',
        (
            # subsidiary with Global Headquarters on the One List
            lambda one_list_tier: CompanyFactory(
                one_list_tier=None,
                global_headquarters=CompanyFactory(one_list_tier=one_list_tier),
            ),
            # subsidiary with Global Headquarters not on the One List
            lambda one_list_tier: CompanyFactory(
                one_list_tier=None,
                global_headquarters=CompanyFactory(one_list_tier=None),
            ),
            # single company on the One List
            lambda one_list_tier: CompanyFactory(
                one_list_tier=one_list_tier,
                global_headquarters=None,
            ),
            # single company not on the One List
            lambda one_list_tier: CompanyFactory(
                one_list_tier=None,
                global_headquarters=None,
            ),
        ),
        ids=(
            'as_subsidiary_of_one_list_company',
            'as_subsidiary_of_non_one_list_company',
            'as_one_list_company',
            'as_non_one_list_company',
        ),
    )
    def test_one_list_group_tier(self, build_company, public_company_api_client):
        """
        Test that the endpoint includes the One List Tier
        of the Global Headquarters in the group.
        """
        one_list_tier = OneListTier.objects.first()
        company = build_company(one_list_tier)

        url = reverse('api-v4:company:public-item', kwargs={'pk': company.pk})
        response = public_company_api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        group_global_headquarters = company.global_headquarters or company

        actual_one_list_group_tier = response.json()['one_list_group_tier']
        if not group_global_headquarters.one_list_tier:
            assert not actual_one_list_group_tier
        else:
            assert actual_one_list_group_tier == {
                'id': str(one_list_tier.id),
                'name': one_list_tier.name,
            }
