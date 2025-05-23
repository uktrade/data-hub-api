import json
import operator
from unittest.mock import patch
from urllib.parse import urljoin
from uuid import UUID, uuid4

import pytest
import requests_mock
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test.utils import override_settings
from faker import Faker
from freezegun import freeze_time
from requests.exceptions import ConnectionError, Timeout
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.constants import OneListTierID
from datahub.company.models import Company, CompanyPermission, OneListTier
from datahub.company.test.factories import CompanyFactory
from datahub.core import constants
from datahub.core.exceptions import APIUpstreamException
from datahub.core.serializers import AddressSerializer
from datahub.core.test_utils import APITestMixin, create_test_user
from datahub.dnb_api.constants import ALL_DNB_UPDATED_SERIALIZER_FIELDS
from datahub.dnb_api.utils import (
    DNBServiceConnectionError,
    DNBServiceTimeoutError,
    format_dnb_company,
)
from datahub.interaction.models import InteractionPermission
from datahub.metadata.models import AdministrativeArea, Country

DNB_V2_SEARCH_URL = urljoin(f'{settings.DNB_SERVICE_BASE_URL}/', 'v2/companies/search/')
DNB_CHANGE_REQUEST_URL = urljoin(f'{settings.DNB_SERVICE_BASE_URL}/', 'change-request/')
DNB_INVESTIGATION_URL = urljoin(f'{settings.DNB_SERVICE_BASE_URL}/', 'investigation/')
DNB_HIERARCHY_SEARCH_URL = urljoin(
    f'{settings.DNB_SERVICE_BASE_URL}/',
    'companies/hierarchy/search/',
)
DNB_HIERARCHY_COUNT_URL = urljoin(DNB_HIERARCHY_SEARCH_URL, 'count')

REQUIRED_REGISTERED_ADDRESS_FIELDS = [
    f'registered_address_{field}' for field in AddressSerializer.REQUIRED_FIELDS
]

URL_PARENT_TRUE_SUBSIDIARY_TRUE = (
    '?include_parent_companies=true&include_subsidiary_companies=true'
)
URL_PARENT_TRUE_SUBSIDIARY_FALSE = (
    '?include_parent_companies=true&include_subsidiary_companies=false'
)
URL_PARENT_FALSE_SUBSIDIARY_TRUE = (
    '?include_parent_companies=false&include_subsidiary_companies=true'
)
URL_PARENT_FALSE_SUBSIDIARY_FALSE = (
    '?include_parent_companies=false&include_subsidiary_companies=false'
)


@pytest.mark.parametrize(
    'url',
    [
        reverse('api-v4:dnb-api:company-search'),
        reverse('api-v4:dnb-api:company-create'),
        reverse('api-v4:dnb-api:company-link'),
        reverse('api-v4:dnb-api:company-change-request'),
    ],
)
class TestDNBAPICommon(APITestMixin):
    """Test common functionality in company-search as well
    as company-create endpoints.
    """

    def test_unauthenticated_not_authorised(
        self,
        requests_mock,
        url,
    ):
        """Ensure that a non-authenticated request gets a 401."""
        requests_mock.post(DNB_V2_SEARCH_URL)

        unauthorised_api_client = self.create_api_client()
        unauthorised_api_client.credentials(HTTP_AUTHORIZATION='foo')

        response = unauthorised_api_client.post(
            url,
            data={'foo': 'bar'},
        )

        assert response.status_code == 401
        assert requests_mock.called is False


class TestDNBCompanySearchAPI(APITestMixin):
    """DNB Company Search view test case."""

    @override_settings(DNB_SERVICE_BASE_URL=None)
    def test_post_no_dnb_setting(self):
        """Test that we get an ImproperlyConfigured exception when the DNB_SERVICE_BASE_URL setting
        is not set.
        """
        with pytest.raises(ImproperlyConfigured):
            self.api_client.post(
                reverse('api-v4:dnb-api:company-search'),
                data={},
            )

    @pytest.mark.parametrize(
        ('content_type', 'expected_status_code'),
        [
            (None, status.HTTP_406_NOT_ACCEPTABLE),
            ('text/html', status.HTTP_406_NOT_ACCEPTABLE),
        ],
    )
    def test_content_type(
        self,
        requests_mock,
        dnb_response_non_uk,
        content_type,
        expected_status_code,
    ):
        """Test that 406 is returned if Content Type is not application/json."""
        requests_mock.post(
            DNB_V2_SEARCH_URL,
            status_code=status.HTTP_200_OK,
            json=dnb_response_non_uk,
        )

        response = self.api_client.post(
            reverse('api-v4:dnb-api:company-search'),
            content_type=content_type,
        )

        assert response.status_code == expected_status_code

    @pytest.mark.parametrize(
        ('request_data', 'response_status_code', 'upstream_response_content', 'response_data'),
        [
            pytest.param(
                b'{"arg": "value"}',
                200,
                b'{"results":[{"duns_number":"9999999"}]}',
                {
                    'results': [
                        {
                            'dnb_company': {'duns_number': '9999999'},
                            'datahub_company': None,
                        },
                    ],
                },
                id='successful call to proxied API with company that cannot be hydrated',
            ),
            pytest.param(
                b'{"arg": "value"}',
                200,
                b'{"results":[{"duns_number":"1234567"}, {"duns_number":"7654321"}]}',
                {
                    'results': [
                        {
                            'dnb_company': {'duns_number': '1234567'},
                            'datahub_company': {
                                'id': '6083b732-b07a-42d6-ada4-c8082293285b',
                                'latest_interaction': None,
                            },
                        },
                        {
                            'dnb_company': {'duns_number': '7654321'},
                            'datahub_company': {
                                'id': '6083b732-b07a-42d6-ada4-c99999999999',
                                'latest_interaction': {
                                    'id': '6083b732-b07a-42d6-ada4-222222222222',
                                    'date': '2019-08-01',
                                    'created_on': '2019-08-01T16:00:00Z',
                                    'subject': 'Meeting with Joe Bloggs',
                                },
                            },
                        },
                    ],
                },
                id='successful call to proxied API with company that can be hydrated',
            ),
        ],
    )
    def test_post_success(
        self,
        dnb_company_search_datahub_companies,
        requests_mock,
        request_data,
        response_status_code,
        upstream_response_content,
        response_data,
    ):
        """Test success scenarios for POST proxy."""
        requests_mock.post(
            DNB_V2_SEARCH_URL,
            status_code=response_status_code,
            content=upstream_response_content,
            headers={'content-type': 'application/json'},
        )

        user = create_test_user(
            permission_codenames=[
                CompanyPermission.view_company,
                InteractionPermission.view_all,
            ],
        )
        api_client = self.create_api_client(user=user)

        url = reverse('api-v4:dnb-api:company-search')
        response = api_client.post(
            url,
            data=request_data,
            content_type='application/json',
        )

        assert response.status_code == response_status_code
        assert response.json() == response_data
        assert requests_mock.last_request.body == request_data

    @pytest.mark.parametrize(
        ('request_data', 'response_status_code', 'upstream_response_content'),
        [
            pytest.param(
                b'{"arg": "value"}',
                400,
                b'{"error":"msg"}',
            ),
            pytest.param(
                b'{"arg": "value"}',
                500,
                b'{"error":"msg"}',
            ),
        ],
    )
    def test_post_errors(
        self,
        dnb_company_search_datahub_companies,
        requests_mock,
        request_data,
        response_status_code,
        upstream_response_content,
    ):
        """Test error scenarios for POST proxy."""
        requests_mock.post(
            DNB_V2_SEARCH_URL,
            status_code=response_status_code,
            content=upstream_response_content,
            headers={'content-type': 'application/json'},
        )

        user = create_test_user(
            permission_codenames=[
                CompanyPermission.view_company,
                InteractionPermission.view_all,
            ],
        )
        api_client = self.create_api_client(user=user)
        url = reverse('api-v4:dnb-api:company-search')

        response = api_client.post(
            url,
            data=request_data,
            content_type='application/json',
        )

        assert response.status_code == response_status_code
        assert requests_mock.last_request.body == request_data

    @pytest.mark.parametrize(
        (
            'response_status_code',
            'upstream_response_content',
            'response_data',
            'permission_codenames',
        ),
        [
            pytest.param(
                200,
                b'{"results":[{"duns_number":"7654321"}]}',
                {
                    'results': [
                        # latest_interaction is omitted, because the user does not have permission
                        # to view interactions
                        {
                            'dnb_company': {'duns_number': '7654321'},
                            'datahub_company': {
                                'id': '6083b732-b07a-42d6-ada4-c99999999999',
                            },
                        },
                    ],
                },
                [CompanyPermission.view_company],
                id=(
                    'successful call to proxied API with company that can be hydrated '
                    'and user that has no interaction permissions'
                ),
            ),
            pytest.param(
                403,
                b'{"error":"msg"}',
                {'detail': 'You do not have permission to perform this action.'},
                [InteractionPermission.view_all],
                id='user missing view_company permission should get a 403',
            ),
            pytest.param(
                200,
                b'{"results":[{"duns_number":"7654321"}]}',
                {
                    'results': [
                        # latest_interaction is None, because the user does not have permission
                        # to view interactions
                        {
                            'dnb_company': {'duns_number': '7654321'},
                            'datahub_company': {
                                'id': '6083b732-b07a-42d6-ada4-c99999999999',
                                'latest_interaction': {
                                    'id': '6083b732-b07a-42d6-ada4-222222222222',
                                    'date': '2019-08-01',
                                    'created_on': '2019-08-01T16:00:00Z',
                                    'subject': 'Meeting with Joe Bloggs',
                                },
                            },
                        },
                    ],
                },
                [CompanyPermission.view_company, InteractionPermission.view_all],
                id=(
                    'user with both view_company and view_all_interaction permissions should get '
                    'a fully hydrated response'
                ),
            ),
        ],
    )
    def test_post_permissions(
        self,
        dnb_company_search_datahub_companies,
        requests_mock,
        response_status_code,
        upstream_response_content,
        response_data,
        permission_codenames,
    ):
        """Test for POST proxy permissions."""
        requests_mock.post(
            DNB_V2_SEARCH_URL,
            status_code=response_status_code,
            content=upstream_response_content,
        )
        user = create_test_user(permission_codenames=permission_codenames)
        api_client = self.create_api_client(user=user)

        url = reverse('api-v4:dnb-api:company-search')
        response = api_client.post(
            url,
            content_type='application/json',
        )
        assert response.status_code == response_status_code
        assert json.loads(response.content) == response_data


class TestDNBCompanyCreateAPI(APITestMixin):
    """DNB Company Create view test case."""

    def _assert_companies_same(self, company, dnb_company):
        """Check whether the given DataHub company is the same as the given DNB company."""
        country = Country.objects.filter(
            iso_alpha2_code=dnb_company['address_country'],
        ).first()

        area = (
            AdministrativeArea.objects.filter(
                area_code=dnb_company['address_area_abbrev_name'],
            ).first()
            if dnb_company.get('address_area_abbrev_name')
            else None
        )

        registered_country = (
            Country.objects.filter(
                iso_alpha2_code=dnb_company['registered_address_country'],
            ).first()
            if dnb_company.get('registered_address_country')
            else None
        )

        company_number = (
            dnb_company['registration_numbers'][0].get('registration_number')
            if country.iso_alpha2_code == 'GB'
            else None
        )

        [company.pop(k) for k in ('id', 'created_on', 'modified_on')]

        required_registered_address_fields_present = all(
            field in dnb_company for field in REQUIRED_REGISTERED_ADDRESS_FIELDS
        )
        registered_address = (
            {
                'area': None,
                'country': {
                    'id': str(registered_country.id),
                    'name': registered_country.name,
                },
                'line_1': dnb_company.get('registered_address_line_1') or '',
                'line_2': dnb_company.get('registered_address_line_2') or '',
                'town': dnb_company.get('registered_address_town') or '',
                'county': dnb_company.get('registered_address_county') or '',
                'postcode': dnb_company.get('registered_address_postcode') or '',
            }
            if required_registered_address_fields_present
            else None
        )

        assert company == {
            'name': dnb_company['primary_name'],
            'trading_names': dnb_company['trading_names'],
            'address': {
                'area': {
                    'id': str(area.id),
                    'name': area.name,
                }
                if area is not None
                else None,
                'country': {
                    'id': str(country.id),
                    'name': country.name,
                },
                'line_1': dnb_company['address_line_1'],
                'line_2': dnb_company['address_line_2'],
                'town': dnb_company['address_town'],
                'county': dnb_company['address_county'],
                'postcode': dnb_company['address_postcode'],
            },
            'registered_address': registered_address,
            'reference_code': '',
            'uk_based': (dnb_company['address_country'] == 'GB'),
            'duns_number': dnb_company['duns_number'],
            'company_number': company_number,
            'number_of_employees': dnb_company['employee_number'],
            'is_number_of_employees_estimated': dnb_company['is_employees_number_estimated'],
            'employee_range': None,
            'turnover': float(dnb_company['annual_sales']),
            'is_turnover_estimated': dnb_company['is_annual_sales_estimated'],
            'turnover_range': None,
            'website': f'http://{dnb_company["domain"]}',
            'business_type': None,
            'description': None,
            'global_headquarters': None,
            'headquarter_type': None,
            'sector': None,
            'export_segment': '',
            'export_sub_segment': '',
            'uk_region': None,
            'vat_number': '',
            'archived': False,
            'archived_by': None,
            'archived_documents_url_path': '',
            'archived_on': None,
            'archived_reason': None,
            'export_experience_category': None,
            'export_potential': None,
            'great_profile_status': None,
            'export_to_countries': [],
            'future_interest_countries': [],
            'one_list_group_global_account_manager': None,
            'one_list_group_tier': None,
            'transfer_reason': '',
            'transferred_by': None,
            'transferred_to': None,
            'transferred_on': None,
            'contacts': [],
            'pending_dnb_investigation': False,
            'global_ultimate_duns_number': dnb_company['global_ultimate_duns_number'],
            'is_global_ultimate': (
                dnb_company['global_ultimate_duns_number'] == dnb_company['duns_number']
            ),
            'dnb_modified_on': '2019-01-01T11:12:13Z',
            'export_countries': [],
            'is_out_of_business': dnb_company['is_out_of_business'],
        }

    @override_settings(DNB_SERVICE_BASE_URL=None)
    def test_post_no_dnb_setting(self):
        """Test that we get an ImproperlyConfigured exception when the DNB_SERVICE_BASE_URL setting
        is not set.
        """
        with pytest.raises(ImproperlyConfigured):
            self.api_client.post(
                reverse('api-v4:dnb-api:company-search'),
                data={'duns_number': '12345678'},
            )

    @freeze_time('2019-01-01 11:12:13')
    def test_post_non_uk(
        self,
        requests_mock,
        dnb_response_non_uk,
    ):
        """Test create-company endpoint for a non-uk company."""
        requests_mock.post(
            DNB_V2_SEARCH_URL,
            json=dnb_response_non_uk,
        )

        response = self.api_client.post(
            reverse('api-v4:dnb-api:company-create'),
            data={
                'duns_number': 123456789,
            },
        )

        assert response.status_code == status.HTTP_200_OK

        company = response.json()
        dnb_company = dnb_response_non_uk['results'].pop()
        self._assert_companies_same(company, dnb_company)

        datahub_company = Company.objects.filter(
            duns_number=company['duns_number'],
        ).first()
        assert datahub_company is not None
        assert datahub_company.created_by == self.user
        assert datahub_company.modified_by == self.user

    @freeze_time('2019-01-01 11:12:13')
    def test_post_uk(
        self,
        requests_mock,
        dnb_response_uk,
    ):
        """Test create-company endpoint for a UK company."""
        requests_mock.post(
            DNB_V2_SEARCH_URL,
            json=dnb_response_uk,
        )

        response = self.api_client.post(
            reverse('api-v4:dnb-api:company-create'),
            data={
                'duns_number': 123456789,
            },
        )

        assert response.status_code == status.HTTP_200_OK

        company = response.json()
        dnb_company = dnb_response_uk['results'].pop()
        self._assert_companies_same(company, dnb_company)

        datahub_company = Company.objects.filter(
            duns_number=company['duns_number'],
        ).first()
        assert datahub_company is not None
        assert datahub_company.created_by == self.user
        assert datahub_company.modified_by == self.user

    @pytest.mark.parametrize(
        'data',
        [
            {'duns_number': None},
            {'duns_number': 'foobarbaz'},
            {'duns_number': '12345678'},
            {'duns_number': '1234567890'},
            {'not_duns_number': '123456789'},
        ],
    )
    def test_post_invalid(
        self,
        data,
    ):
        """Test that a query without `duns_number` returns 400."""
        response = self.api_client.post(
            reverse('api-v4:dnb-api:company-create'),
            data=data,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.parametrize(
        ('results', 'expected_status_code', 'expected_message'),
        [
            (
                [],
                400,
                'Cannot find a company with duns_number: 123456789',
            ),
            (
                ['foo', 'bar'],
                502,
                'Multiple companies found with duns_number: 123456789',
            ),
            (
                [{'duns_number': '012345678'}],
                502,
                'DUNS number of the company: 012345678 '
                'did not match searched DUNS number: 123456789',
            ),
        ],
    )
    def test_post_none_or_multiple_companies_found(
        self,
        requests_mock,
        results,
        expected_status_code,
        expected_message,
    ):
        """Test if a given `duns_number` gets anything other than a single company
        from dnb-service, the create-company endpoint returns a 400.

        """
        requests_mock.post(
            DNB_V2_SEARCH_URL,
            json={'results': results},
        )

        response = self.api_client.post(
            reverse('api-v4:dnb-api:company-create'),
            data={
                'duns_number': 123456789,
            },
        )

        assert response.status_code == expected_status_code
        assert response.json()['detail'] == expected_message

    @pytest.mark.parametrize(
        ('missing_required_field', 'expected_error'),
        [
            ('primary_name', {'name': ['This field may not be null.']}),
            ('trading_names', {'trading_names': ['This field may not be null.']}),
            ('address_line_1', {'address': {'line_1': ['This field is required.']}}),
            ('address_town', {'address': {'town': ['This field is required.']}}),
            ('address_country', {'address': {'country': ['This field is required.']}}),
        ],
    )
    def test_post_missing_required_fields(
        self,
        requests_mock,
        dnb_response_uk,
        missing_required_field,
        expected_error,
    ):
        """Test if dnb-service returns a company with missing required fields,
        the create-company endpoint returns 400.
        """
        dnb_response_uk['results'][0].pop(missing_required_field)
        requests_mock.post(
            DNB_V2_SEARCH_URL,
            json=dnb_response_uk,
        )

        response = self.api_client.post(
            reverse('api-v4:dnb-api:company-create'),
            data={
                'duns_number': 123456789,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == expected_error

    @pytest.mark.parametrize(
        'field_overrides',
        [
            {'domain': None},
            {'trading_names': []},
            {'annual_sales': None},
            {'employee_number': None},
            {'is_employee_number_estimated': None},
            {'registered_address_line_1': ''},
            {'registered_address_line_2': ''},
            {'registered_address_town': ''},
            {'registered_address_county': ''},
            {'registered_address_postcode': ''},
            {'registered_address_country': ''},
            {'address_line_2': ''},
            {'address_county': ''},
            {'address_postcode': ''},
            {'global_ultimate_duns_number': None},
        ],
    )
    def test_post_missing_optional_fields(
        self,
        requests_mock,
        dnb_response_uk,
        field_overrides,
    ):
        """Test if dnb-service returns a company with missing optional fields,
        the create-company endpoint still returns 200 and the company is saved
        successfully.
        """
        dnb_response_uk['results'][0].update(field_overrides)
        requests_mock.post(
            DNB_V2_SEARCH_URL,
            json=dnb_response_uk,
        )

        response = self.api_client.post(
            reverse('api-v4:dnb-api:company-create'),
            data={
                'duns_number': 123456789,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        created_company = Company.objects.first()
        assert created_company.name == dnb_response_uk['results'][0]['primary_name']
        overridden_fields = field_overrides.keys()
        if any(field in overridden_fields for field in REQUIRED_REGISTERED_ADDRESS_FIELDS):
            assert created_company.registered_address_1 == ''
            assert created_company.registered_address_2 == ''
            assert created_company.registered_address_town == ''
            assert created_company.registered_address_county == ''
            assert created_company.registered_address_country is None
            assert created_company.registered_address_postcode == ''

    def test_post_existing(
        self,
    ):
        """Test if create-company endpoint returns 400 if the company with the given
        duns_number already exists in DataHub.
        """
        duns_number = 123456789
        CompanyFactory(duns_number=duns_number)

        response = self.api_client.post(
            reverse('api-v4:dnb-api:company-create'),
            data={
                'duns_number': duns_number,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'duns_number': [f'Company with duns_number: {duns_number} already exists in DataHub.'],
        }

    def test_post_invalid_country(
        self,
        requests_mock,
        dnb_response_uk,
    ):
        """Test if create-company endpoint returns 400 if the company is based in a country
        that does not exist in DataHub.
        """
        dnb_response_uk['results'][0]['address_country'] = 'FOO'
        requests_mock.post(
            DNB_V2_SEARCH_URL,
            json=dnb_response_uk,
        )

        response = self.api_client.post(
            reverse('api-v4:dnb-api:company-create'),
            data={
                'duns_number': 123456789,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.parametrize(
        'global_ultimate_override',
        [
            {'global_ultimate_duns_number': 'foobarbaz'},
            {'global_ultimate_duns_number': '12345678'},
            {'global_ultimate_duns_number': '1234567890'},
        ],
    )
    def test_post_invalid_global_ultimate(
        self,
        requests_mock,
        dnb_response_uk,
        global_ultimate_override,
    ):
        """Test if create-company endpoint returns 400 if the global_ultimate_duns_number
        returned from D&B is invalid.
        """
        dnb_response_uk['results'][0]['global_ultimate_duns_number'] = global_ultimate_override
        requests_mock.post(
            DNB_V2_SEARCH_URL,
            json=dnb_response_uk,
        )

        response = self.api_client.post(
            reverse('api-v4:dnb-api:company-create'),
            data={
                'duns_number': 123456789,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.parametrize(
        'status_code',
        [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_405_METHOD_NOT_ALLOWED,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            status.HTTP_502_BAD_GATEWAY,
        ],
    )
    def test_post_dnb_service_error(
        self,
        requests_mock,
        status_code,
    ):
        """Test if create-company endpoint returns 400 if the company is based in a country
        that does not exist in DataHub.
        """
        requests_mock.post(
            DNB_V2_SEARCH_URL,
            status_code=status_code,
        )

        response = self.api_client.post(
            reverse('api-v4:dnb-api:company-create'),
            data={
                'duns_number': 123456789,
            },
        )

        assert response.status_code == status.HTTP_502_BAD_GATEWAY

    def test_post_dnb_service_connection_error(
        self,
        requests_mock,
    ):
        """Test if create-company endpoint returns 400 if the company is based in a country
        that does not exist in DataHub.
        """
        requests_mock.post(
            DNB_V2_SEARCH_URL,
            exc=ConnectionError('An error occurred'),
        )

        response = self.api_client.post(
            reverse('api-v4:dnb-api:company-create'),
            data={
                'duns_number': 123456789,
            },
        )

        assert response.status_code == status.HTTP_502_BAD_GATEWAY

    @pytest.mark.parametrize(
        'permissions',
        [
            [],
            [CompanyPermission.add_company],
            [CompanyPermission.view_company],
        ],
    )
    def test_post_no_permission(
        self,
        requests_mock,
        dnb_response_uk,
        permissions,
    ):
        """Create-company endpoint should return 403 if the user does not
        have the necessary permissions.
        """
        requests_mock.post(
            DNB_V2_SEARCH_URL,
            json=dnb_response_uk,
        )

        user = create_test_user(permission_codenames=permissions)
        api_client = self.create_api_client(user=user)
        response = api_client.post(
            reverse('api-v4:dnb-api:company-create'),
            data={
                'duns_number': 123456789,
            },
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestCompanyLinkView(APITestMixin):
    """Test POST `/dnb/company-link` endpoint."""

    @pytest.mark.parametrize(
        ('content_type', 'expected_status_code'),
        [
            (None, status.HTTP_406_NOT_ACCEPTABLE),
            ('text/html', status.HTTP_406_NOT_ACCEPTABLE),
        ],
    )
    def test_content_type(
        self,
        content_type,
        expected_status_code,
    ):
        """Test that 406 is returned if Content Type is not application/json."""
        response = self.api_client.post(
            reverse('api-v4:dnb-api:company-link'),
            content_type=content_type,
        )

        assert response.status_code == expected_status_code

    @pytest.mark.parametrize(
        'permissions',
        [
            [],
            [CompanyPermission.change_company],
            [CompanyPermission.view_company],
        ],
    )
    def test_no_permission(
        self,
        permissions,
    ):
        """The endpoint should return 403 if the user does not have the necessary permissions."""
        user = create_test_user(permission_codenames=permissions)
        api_client = self.create_api_client(user=user)
        response = api_client.post(
            reverse('api-v4:dnb-api:company-link'),
            data={},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize(
        'override',
        [
            {'duns_number': None},
            {'duns_number': 'foobarbaz'},
            {'duns_number': '12345678'},
            {'duns_number': '1234567890'},
            {'company_id': None},
            {'company_id': 'does-not-exist'},
            {'company_id': '11111111-2222-3333-4444-555555555555'},
        ],
    )
    def test_invalid(
        self,
        override,
    ):
        """Test that a query without a valid `duns_number` returns 400."""
        company = CompanyFactory()
        response = self.api_client.post(
            reverse('api-v4:dnb-api:company-link'),
            data={
                'company_id': company.pk,
                **override,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.parametrize(
        'status_code',
        [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_405_METHOD_NOT_ALLOWED,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            status.HTTP_502_BAD_GATEWAY,
        ],
    )
    def test_dnb_service_error(
        self,
        requests_mock,
        status_code,
    ):
        """Test if company-link endpoint returns 502 if the upstream
        `dnb-service` returns an error.
        """
        company = CompanyFactory()
        requests_mock.post(
            DNB_V2_SEARCH_URL,
            status_code=status_code,
        )

        response = self.api_client.post(
            reverse('api-v4:dnb-api:company-link'),
            data={
                'company_id': company.id,
                'duns_number': 123456789,
            },
        )

        assert response.status_code == status.HTTP_502_BAD_GATEWAY

    def test_already_linked(self):
        """Test that the endpoint returns 400 for a company that is already linked."""
        company = CompanyFactory(duns_number='123456789')
        response = self.api_client.post(
            reverse('api-v4:dnb-api:company-link'),
            data={
                'company_id': company.pk,
                'duns_number': '012345678',
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'detail': f'Company {str(company.id)} is already linked with duns number 123456789',
        }

    def test_duplicate_duns_number(self):
        """Test that the endpoint returns 400 if we try to link a company to a D&B record
        that has already been linked to a different company.
        """
        CompanyFactory(duns_number='123456789')
        company = CompanyFactory()
        response = self.api_client.post(
            reverse('api-v4:dnb-api:company-link'),
            data={
                'company_id': company.pk,
                'duns_number': '123456789',
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'duns_number': ['Company with duns_number: 123456789 already exists in DataHub.'],
        }

    def test_company_not_found(
        self,
        requests_mock,
    ):
        """Test that when a duns_number does not return any company from
        dnb-service, the endpoint returns 400 status.
        """
        company = CompanyFactory()
        requests_mock.post(
            DNB_V2_SEARCH_URL,
            status_code=status.HTTP_200_OK,
            json={'results': []},
        )
        response = self.api_client.post(
            reverse('api-v4:dnb-api:company-link'),
            data={
                'company_id': company.pk,
                'duns_number': '123456789',
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'detail': 'Cannot find a company with duns_number: 123456789',
        }

    def test_valid(
        self,
        requests_mock,
        dnb_response_uk,
    ):
        """Test that valid request to company-link endpoint returns 200."""
        company = CompanyFactory()
        requests_mock.post(
            DNB_V2_SEARCH_URL,
            status_code=status.HTTP_200_OK,
            json=dnb_response_uk,
        )
        response = self.api_client.post(
            reverse('api-v4:dnb-api:company-link'),
            data={
                'company_id': company.pk,
                'duns_number': '123456789',
            },
        )
        assert response.status_code == status.HTTP_200_OK

        dh_company = response.json()
        dnb_company = format_dnb_company(dnb_response_uk['results'][0])
        # TODO: The format for the payload returned via CompanySerializer and that returned via
        # format_dnb_company is slightly different.
        # format_dnb_company: {... 'country': UUID(...)}
        # CompanySerializer: {... 'country': {'id': <uuid:str>}}
        dh_company['address']['country'] = UUID(dh_company['address']['country']['id'])

        for field in ALL_DNB_UPDATED_SERIALIZER_FIELDS:
            assert dh_company[field] == dnb_company[field]


class TestCompanyChangeRequestView(APITestMixin):
    """Test POST `/dnb/company-change-request` endpoint."""

    @pytest.mark.parametrize(
        ('content_type', 'expected_status_code'),
        [
            (None, status.HTTP_406_NOT_ACCEPTABLE),
            ('text/html', status.HTTP_406_NOT_ACCEPTABLE),
        ],
    )
    def test_content_type(
        self,
        content_type,
        expected_status_code,
    ):
        """Test that 406 is returned if Content Type is not application/json."""
        response = self.api_client.post(
            reverse('api-v4:dnb-api:company-change-request'),
            content_type=content_type,
        )

        assert response.status_code == expected_status_code

    @pytest.mark.parametrize(
        'permissions',
        [
            [],
            [CompanyPermission.change_company],
            [CompanyPermission.view_company],
        ],
    )
    def test_no_permission(
        self,
        permissions,
    ):
        """The endpoint should return 403 if the user does not have the necessary permissions."""
        user = create_test_user(permission_codenames=permissions)
        api_client = self.create_api_client(user=user)
        response = api_client.post(
            reverse('api-v4:dnb-api:company-change-request'),
            data={},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_company_does_not_exist(self):
        """The endpoint should return 400 if the company with the given
        duns_number does not exist.
        """
        response = self.api_client.post(
            reverse('api-v4:dnb-api:company-change-request'),
            data={
                'duns_number': '123456789',
                'changes': {
                    'name': 'Foo Bar',
                },
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'duns_number': [
                'Company with duns_number: 123456789 does not exists in DataHub.',
            ],
        }

    @pytest.mark.parametrize(
        ('change_request', 'expected_response'),
        [
            # No changes
            (
                {
                    'duns_number': '123456789',
                },
                {
                    'changes': ['This field is required.'],
                },
            ),
            # No duns_number
            (
                {
                    'changes': {
                        'website': 'example.com',
                    },
                },
                {
                    'duns_number': ['This field is required.'],
                },
            ),
            # Empty changes
            (
                {
                    'duns_number': '123456789',
                    'changes': {},
                },
                {
                    'changes': ['No changes submitted.'],
                },
            ),
            # Invalid website
            (
                {
                    'duns_number': '123456789',
                    'changes': {
                        'website': 'Foo Bar',
                    },
                },
                {
                    'changes': {
                        'website': ['Enter a valid URL.'],
                    },
                },
            ),
        ],
    )
    def test_invalid_fields(
        self,
        change_request,
        expected_response,
    ):
        """Test that invalid payload results in 400 and an appropriate
        error message.
        """
        CompanyFactory(duns_number='123456789')

        response = self.api_client.post(
            reverse('api-v4:dnb-api:company-change-request'),
            data=change_request,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == expected_response

    @pytest.mark.parametrize(
        ('change_request', 'dnb_request', 'dnb_response', 'datahub_response', 'address_area_id'),
        [
            # All valid fields
            (
                # change_request
                {
                    'duns_number': '123456789',
                    'changes': {
                        'name': 'Foo Bar',
                        'trading_names': ['Foo Bar INC'],
                        'website': 'https://example.com',
                        'address': {
                            'line_1': '123 Fake Street',
                            'line_2': 'Foo',
                            'town': 'Beverly Hills',
                            'county': 'Los Angeles',
                            'area': {
                                'id': constants.AdministrativeArea.alabama.value.id,
                            },
                            'postcode': '91012',
                            'country': {
                                'id': constants.Country.united_states.value.id,
                            },
                        },
                        'number_of_employees': 100,
                        'turnover': 1000,
                    },
                },
                # dnb_request
                {
                    'duns_number': '123456789',
                    'changes': {
                        'primary_name': 'Foo Bar',
                        'trading_names': ['Foo Bar INC'],
                        'domain': 'example.com',
                        'address_line_1': '123 Fake Street',
                        'address_line_2': 'Foo',
                        'address_town': 'Beverly Hills',
                        'address_county': 'Los Angeles',
                        'address_area': {
                            'name': 'Alabama',
                            'abbrev_name': 'AL',
                        },
                        'address_country': 'US',
                        'address_postcode': '91012',
                        'employee_number': 100,
                        'annual_sales': 1000,
                    },
                },
                # dnb_response
                {
                    'duns_number': '123456789',
                    'id': '11111111-2222-3333-4444-555555555555',
                    'status': 'pending',
                    'created_on': '2020-01-05T11:00:00',
                    'changes': {
                        'primary_name': 'Foo Bar',
                        'trading_names': ['Foo Bar INC'],
                        'domain': 'example.com',
                        'address_line_1': '123 Fake Street',
                        'address_line_2': 'Foo',
                        'address_town': 'Beverly Hills',
                        'address_county': 'Los Angeles',
                        'address_area': {
                            'name': 'Alabama',
                            'abbrev_name': 'AL',
                        },
                        'address_country': 'US',
                        'address_postcode': '91012',
                        'employee_number': 100,
                        'annual_sales': 1000,
                    },
                },
                # datahub_response
                {
                    'duns_number': '123456789',
                    'id': '11111111-2222-3333-4444-555555555555',
                    'status': 'pending',
                    'created_on': '2020-01-05T11:00:00',
                    'changes': {
                        'primary_name': 'Foo Bar',
                        'trading_names': ['Foo Bar INC'],
                        'domain': 'example.com',
                        'address_line_1': '123 Fake Street',
                        'address_line_2': 'Foo',
                        'address_town': 'Beverly Hills',
                        'address_county': 'Los Angeles',
                        'address_area': {
                            'name': 'Alabama',
                            'abbrev_name': 'AL',
                        },
                        'address_country': 'US',
                        'address_postcode': '91012',
                        'employee_number': 100,
                        'annual_sales': 1000,
                    },
                },
                # Address Area id (of initial Company)
                None,
            ),
            # Website - domain
            (
                # change_request
                {
                    'duns_number': '123456789',
                    'changes': {
                        'website': 'https://example.com/hello',
                    },
                },
                # dnb_request
                {
                    'duns_number': '123456789',
                    'changes': {
                        'domain': 'example.com',
                    },
                },
                # dnb_response
                {
                    'duns_number': '123456789',
                    'id': '11111111-2222-3333-4444-555555555555',
                    'status': 'pending',
                    'created_on': '2020-01-05T11:00:00',
                    'changes': {
                        'domain': 'example.com',
                    },
                },
                # datahub_response
                {
                    'duns_number': '123456789',
                    'id': '11111111-2222-3333-4444-555555555555',
                    'status': 'pending',
                    'created_on': '2020-01-05T11:00:00',
                    'changes': {
                        'domain': 'example.com',
                    },
                },
                # Address Area id (of initial Company)
                None,
            ),
            # Address area is not selected, but is associated
            (
                # change_request
                {
                    'duns_number': '123456789',
                    'changes': {
                        'name': 'Foo Bar',
                        'trading_names': ['Foo Bar INC'],
                        'website': 'https://example.com',
                        'address': {
                            'line_1': '123 Fake Street',
                            'line_2': 'Foo',
                            'town': 'London',
                            'county': 'Greater London',
                            'area_name': '',
                            'area_abbrev_name': '',
                            'postcode': 'W1 0TN',
                            'country': {
                                'id': constants.Country.united_kingdom.value.id,
                            },
                        },
                        'number_of_employees': 100,
                        'turnover': 1000,
                    },
                },
                # dnb_request
                {
                    'duns_number': '123456789',
                    'changes': {
                        'primary_name': 'Foo Bar',
                        'trading_names': ['Foo Bar INC'],
                        'domain': 'example.com',
                        'address_line_1': '123 Fake Street',
                        'address_line_2': 'Foo',
                        'address_town': 'London',
                        'address_county': 'Greater London',
                        'address_area': {
                            'name': constants.AdministrativeArea.texas.value.name,
                            'abbrev_name': constants.AdministrativeArea.texas.value.area_code,
                        },
                        'address_country': 'GB',
                        'address_postcode': 'W1 0TN',
                        'employee_number': 100,
                        'annual_sales': 1000,
                    },
                },
                # dnb_response
                {
                    'duns_number': '123456789',
                    'id': '11111111-2222-3333-4444-555555555555',
                    'status': 'pending',
                    'created_on': '2020-01-05T11:00:00',
                    'changes': {
                        'primary_name': 'Foo Bar',
                        'trading_names': ['Foo Bar INC'],
                        'domain': 'example.com',
                        'address_line_1': '123 Fake Street',
                        'address_line_2': 'Foo',
                        'address_town': 'London',
                        'address_county': 'Greater London',
                        'address_country': 'GB',
                        'address_area': {
                            'name': constants.AdministrativeArea.texas.value.name,
                            'abbrev_name': constants.AdministrativeArea.texas.value.area_code,
                        },
                        'address_postcode': 'W1 0TN',
                        'employee_number': 100,
                        'annual_sales': 1000,
                    },
                },
                # datahub_response
                {
                    'duns_number': '123456789',
                    'id': '11111111-2222-3333-4444-555555555555',
                    'status': 'pending',
                    'created_on': '2020-01-05T11:00:00',
                    'changes': {
                        'primary_name': 'Foo Bar',
                        'trading_names': ['Foo Bar INC'],
                        'domain': 'example.com',
                        'address_line_1': '123 Fake Street',
                        'address_line_2': 'Foo',
                        'address_town': 'London',
                        'address_county': 'Greater London',
                        'address_area': {
                            'name': constants.AdministrativeArea.texas.value.name,
                            'abbrev_name': constants.AdministrativeArea.texas.value.area_code,
                        },
                        'address_country': 'GB',
                        'address_postcode': 'W1 0TN',
                        'employee_number': 100,
                        'annual_sales': 1000,
                    },
                },
                # Address Area id (of initial Company)
                constants.AdministrativeArea.texas.value.id,
            ),
            # Test turnover_gbp converted correctly
            (
                # change_request
                {
                    'duns_number': '123456789',
                    'changes': {
                        'turnover_gbp': 725,
                    },
                },
                # dnb_request
                {
                    'duns_number': '123456789',
                    'changes': {
                        'annual_sales': 1000.1327348575835,
                    },
                },
                # dnb_response
                {
                    'duns_number': '123456789',
                    'id': '11111111-2222-3333-4444-555555555555',
                    'status': 'pending',
                    'created_on': '2020-01-05T11:00:00',
                    'changes': {
                        'annual_sales': 1000.1327348575835,
                    },
                },
                # datahub_response
                {
                    'duns_number': '123456789',
                    'id': '11111111-2222-3333-4444-555555555555',
                    'status': 'pending',
                    'created_on': '2020-01-05T11:00:00',
                    'changes': {
                        'annual_sales': 1000.1327348575835,
                    },
                },
                # Address Area id (of initial Company)
                None,
            ),
        ],
    )
    def test_valid(
        self,
        requests_mock,
        change_request,
        dnb_request,
        dnb_response,
        datahub_response,
        address_area_id,
    ):
        """The endpoint should return 200 as well as a valid response
        when it is hit with a valid payload.
        """
        CompanyFactory(
            duns_number='123456789',
            address_area_id=address_area_id,
        )

        requests_mock.post(
            DNB_CHANGE_REQUEST_URL,
            status_code=status.HTTP_201_CREATED,
            json=dnb_response,
        )

        with patch('datahub.metadata.utils.get_latest_exchange_rate', return_value=0.72490378):
            response = self.api_client.post(
                reverse('api-v4:dnb-api:company-change-request'),
                data=change_request,
            )

        assert requests_mock.last_request.json() == dnb_request
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == datahub_response

    @pytest.mark.parametrize(
        'status_code',
        [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_405_METHOD_NOT_ALLOWED,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            status.HTTP_502_BAD_GATEWAY,
        ],
    )
    def test_dnb_service_error(
        self,
        requests_mock,
        status_code,
    ):
        """The  endpoint should return 502 if the upstream
        `dnb-service` returns an error.
        """
        CompanyFactory(duns_number='123456789')
        requests_mock.post(
            DNB_CHANGE_REQUEST_URL,
            status_code=status_code,
        )

        response = self.api_client.post(
            reverse('api-v4:dnb-api:company-change-request'),
            data={
                'duns_number': '123456789',
                'changes': {
                    'website': 'www.example.com',
                },
            },
        )

        assert response.status_code == status.HTTP_502_BAD_GATEWAY

    @override_settings(DNB_SERVICE_BASE_URL=None)
    def test_post_no_dnb_setting(self):
        """Test that we get an ImproperlyConfigured exception when the DNB_SERVICE_BASE_URL setting
        is not set.
        """
        CompanyFactory(duns_number='123456789')

        with pytest.raises(ImproperlyConfigured):
            self.api_client.post(
                reverse('api-v4:dnb-api:company-change-request'),
                data={
                    'duns_number': '123456789',
                    'changes': {
                        'website': 'www.example.com',
                    },
                },
            )

    @pytest.mark.parametrize(
        ('request_exception', 'expected_exception', 'expected_message'),
        [
            (
                ConnectionError,
                DNBServiceConnectionError,
                'Encountered an error connecting to DNB service',
            ),
            (
                Timeout,
                DNBServiceTimeoutError,
                'Encountered a timeout interacting with DNB service',
            ),
        ],
    )
    def test_request_error(
        self,
        requests_mock,
        request_exception,
        expected_exception,
        expected_message,
    ):
        """Test if there is an error connecting to dnb-service, we raise the
        exception with an appropriate message.
        """
        CompanyFactory(duns_number='123456789')
        requests_mock.post(
            DNB_CHANGE_REQUEST_URL,
            exc=request_exception,
        )

        response = self.api_client.post(
            reverse('api-v4:dnb-api:company-change-request'),
            data={
                'duns_number': '123456789',
                'changes': {
                    'website': 'www.example.com',
                },
            },
        )

        assert response.status_code == status.HTTP_502_BAD_GATEWAY

    def test_partial_address(
        self,
        requests_mock,
    ):
        """Test that a partial change-request to address sends
        all address fields to dnb-service.
        """
        address_area_id = constants.AdministrativeArea.texas.value.id
        company = CompanyFactory(
            duns_number='123456789',
            address_area_id=address_area_id,
        )
        requests_mock.post(
            DNB_CHANGE_REQUEST_URL,
            status_code=status.HTTP_201_CREATED,
            json={
                'id': '11111111-2222-3333-4444-555555555555',
                'status': 'pending',
                'created_on': '2020-01-05T11:00:00',
                'duns_number': '123456789',
                'changes': {
                    'address_line_1': f'New {company.address_1}',
                    'address_line_2': company.address_2,
                    'address_town': company.address_town,
                    'address_county': company.address_county,
                    'address_country': company.address_country.iso_alpha2_code,
                    'address_postcode': company.address_postcode,
                    'address_area': {
                        'id': address_area_id,
                    },
                },
            },
        )

        response = self.api_client.post(
            reverse('api-v4:dnb-api:company-change-request'),
            data={
                'duns_number': '123456789',
                'changes': {
                    'address': {
                        'line_1': f'New {company.address_1}',
                    },
                },
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert requests_mock.last_request.json() == {
            'duns_number': '123456789',
            'changes': {
                'address_line_1': f'New {company.address_1}',
                'address_line_2': company.address_2,
                'address_town': company.address_town,
                'address_county': company.address_county,
                'address_country': company.address_country.iso_alpha2_code,
                'address_postcode': company.address_postcode,
                'address_area': {
                    'name': constants.AdministrativeArea.texas.value.name,
                    'abbrev_name': constants.AdministrativeArea.texas.value.area_code,
                },
            },
        }

    @pytest.mark.parametrize(
        ('request_exception', 'expected_exception', 'expected_message'),
        [
            (
                ConnectionError,
                DNBServiceConnectionError,
                'Encountered an error connecting to DNB service',
            ),
            (
                Timeout,
                DNBServiceTimeoutError,
                'Encountered a timeout interacting with DNB service',
            ),
        ],
    )
    def test_get_request_error(
        self,
        requests_mock,
        request_exception,
        expected_exception,
        expected_message,
    ):
        """Test if there is an error connecting to dnb-service, we raise the
        exception with an appropriate message.
        """
        CompanyFactory(duns_number='123456789')
        requests_mock.get(
            DNB_CHANGE_REQUEST_URL,
            exc=request_exception,
        )

        response = self.api_client.get(
            reverse('api-v4:dnb-api:company-change-request'),
            {'duns_number': '123456789', 'status': 'pending'},
            content_type='application/json',
        )
        assert response.status_code == status.HTTP_502_BAD_GATEWAY

    @pytest.mark.parametrize(
        ('dnb_request', 'dnb_response'),
        [
            (
                # dnb_request
                {
                    'duns_number': '123456789',
                    'status': 'pending',
                },
                # dnb_response
                {
                    'duns_number': '123456789',
                    'id': '11111111-2222-3333-4444-555555555555',
                    'status': 'pending',
                    'created_on': '2020-01-05T11:00:00',
                    'changes': {
                        'primary_name': 'Foo Bar',
                        'trading_names': ['Foo Bar INC'],
                        'domain': 'example.com',
                        'address_line_1': '123 Fake Street',
                        'address_line_2': 'Foo',
                        'address_town': 'London',
                        'address_county': 'Greater London',
                        'address_country': 'GB',
                        'address_postcode': 'W1 0TN',
                        'employee_number': 100,
                        'annual_sales': 1000,
                    },
                },
            ),
            (
                # dnb_request
                {
                    'duns_number': '123456789',
                },
                # dnb_response
                {
                    'duns_number': '123456789',
                    'id': '11111111-2222-3333-4444-555555555555',
                    'status': 'pending',
                    'created_on': '2020-01-05T11:00:00',
                    'changes': {
                        'primary_name': 'Foo Bar',
                        'trading_names': ['Foo Bar INC'],
                        'domain': 'example.com',
                        'address_line_1': '123 Fake Street',
                        'address_line_2': 'Foo',
                        'address_town': 'London',
                        'address_county': 'Greater London',
                        'address_country': 'GB',
                        'address_postcode': 'W1 0TN',
                        'employee_number': 100,
                        'annual_sales': 1000,
                    },
                },
            ),
        ],
    )
    def test_that_pending_request_returns_correctly(
        self,
        requests_mock,
        dnb_request,
        dnb_response,
    ):
        """Test that pending change requests stored in the dnb-service can be
        retrieved correctly.
        """
        CompanyFactory(duns_number=dnb_request['duns_number'])
        requests_mock.get(
            DNB_CHANGE_REQUEST_URL,
            status_code=status.HTTP_201_CREATED,
            json=dnb_response,
        )

        response = self.api_client.get(
            reverse('api-v4:dnb-api:company-change-request'),
            data=dnb_request,
            content_type='application/json',
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == dnb_response

    @pytest.mark.parametrize(
        ('change_request', 'expected_response'),
        [
            # No duns_number
            (
                {
                    'status': 'pending',
                },
                {
                    'duns_number': ['This field may not be null.'],
                },
            ),
            # Invalid duns_number
            (
                {
                    'duns_number': 'something invalid',
                    'status': 'pending',
                },
                {
                    'duns_number': [
                        'Enter a valid integer.',
                        'Ensure this field has no more than 9 characters.',
                    ],
                },
            ),
            # Invalid status
            (
                {
                    'duns_number': '123456789',
                    'status': 'something invalid',
                },
                {
                    'status': ['"something invalid" is not a valid choice.'],
                },
            ),
        ],
    )
    def test_invalid_fields_for_get(
        self,
        change_request,
        expected_response,
    ):
        """Test that invalid payload results in 400 and an appropriate
        error message.
        """
        CompanyFactory(duns_number='123456789')

        response = self.api_client.get(
            reverse('api-v4:dnb-api:company-change-request'),
            change_request,
            content_type='application/json',
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == expected_response


class TestCompanyInvestigationView(APITestMixin):
    """Test POST `/dnb/company-investigation` endpoint."""

    @pytest.mark.parametrize(
        ('content_type', 'expected_status_code'),
        [
            (None, status.HTTP_406_NOT_ACCEPTABLE),
            ('text/html', status.HTTP_406_NOT_ACCEPTABLE),
        ],
    )
    def test_content_type(
        self,
        content_type,
        expected_status_code,
    ):
        """Test that 406 is returned if Content Type is not application/json."""
        response = self.api_client.post(
            reverse('api-v4:dnb-api:company-investigation'),
            content_type=content_type,
        )

        assert response.status_code == expected_status_code

    def test_unauthenticated_not_authorised(self):
        """Ensure that a non-authenticated request gets a 401."""
        unauthorised_api_client = self.create_api_client()
        unauthorised_api_client.credentials(HTTP_AUTHORIZATION='foo')

        response = unauthorised_api_client.post(
            reverse('api-v4:dnb-api:company-investigation'),
            data={},
        )

        assert response.status_code == 401

    @pytest.mark.parametrize(
        'permissions',
        [
            [],
            [CompanyPermission.change_company],
            [CompanyPermission.view_company],
        ],
    )
    def test_no_permission(
        self,
        permissions,
    ):
        """The endpoint should return 403 if the user does not have the necessary permissions."""
        user = create_test_user(permission_codenames=permissions)
        api_client = self.create_api_client(user=user)
        response = api_client.post(
            reverse('api-v4:dnb-api:company-investigation'),
            data={},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_company_does_not_exist(self):
        """The endpoint should return 400 if the company when the given company ID does not exist."""
        response = self.api_client.post(
            reverse('api-v4:dnb-api:company-investigation'),
            data={
                'company': '5cf5bf52-9497-465d-913b-f8fdc0331f41',
                'name': 'Foo Bar LTD',
                'address': {
                    'line_1': '123 Fake Street',
                    'line_2': 'Someplace',
                    'town': 'London',
                    'county': 'Greater London',
                    'country': {
                        'id': constants.Country.united_kingdom.value.id,
                    },
                    'postcode': 'W1 0TN',
                },
                'website': 'https://www.example.com',
                'telephone_number': '+44 1234 567 890',
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'company': [
                'Invalid pk "5cf5bf52-9497-465d-913b-f8fdc0331f41" - object does not exist.',
            ],
        }

    @pytest.mark.parametrize(
        ('investigation_request_overrides', 'expected_response'),
        [
            # No name
            (
                {
                    'name': None,
                },
                {
                    'name': ['This field may not be null.'],
                },
            ),
            # No address
            (
                {
                    'address': None,
                },
                {
                    'address': ['This field may not be null.'],
                },
            ),
            # Address missing required fields
            (
                {
                    'address': {
                        'postcode': 'W1 0TN',
                    },
                },
                {
                    'address': {
                        'line_1': ['This field is required.'],
                        'town': ['This field is required.'],
                        'country': ['This field is required.'],
                    },
                },
            ),
            # No website or phone number
            (
                {
                    'website': '',
                    'telephone_number': '',
                },
                {
                    'non_field_errors': [
                        'Either website or telephone_number must be provided.',
                    ],
                },
            ),
            # Invalid website
            (
                {
                    'website': 'Foo Bar',
                },
                {
                    'website': ['Enter a valid URL.'],
                },
            ),
        ],
    )
    def test_invalid_fields(
        self,
        investigation_request_overrides,
        expected_response,
    ):
        """Test that invalid payload results in 400 and an appropriate error message."""
        company = CompanyFactory()
        investigation_data = {
            'company': company.id,
            'name': 'Foo Bar LTD',
            'address': {
                'line_1': '123 Fake Street',
                'line_2': 'Someplace',
                'town': 'London',
                'county': 'Greater London',
                'country': {
                    'id': constants.Country.united_kingdom.value.id,
                },
                'postcode': 'W1 0TN',
            },
            'website': 'https://www.example.com',
            'telephone_number': '+44 1234 567 890',
            **investigation_request_overrides,
        }

        response = self.api_client.post(
            reverse('api-v4:dnb-api:company-investigation'),
            data=investigation_data,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == expected_response

    def test_valid_full_data(
        self,
        requests_mock,
    ):
        """The endpoint should return 200 as well as a valid response when it is hit with a valid
        payload of full investigation details.
        """
        company = CompanyFactory(
            address_area_id=constants.AdministrativeArea.new_york.value.id,
        )
        dnb_formatted_company_details = {
            'company_details': {
                'primary_name': 'Joe Bloggs LTD',
                'domain': 'www.example.com',
                'telephone_number': '123456789',
                'address_line_1': '23 Code Street',
                'address_line_2': 'Someplace',
                'address_town': 'Beverly Hills',
                'address_county': 'Los Angeles',
                'address_area': {
                    'name': constants.AdministrativeArea.new_york.value.name,
                    'abbrev_name': constants.AdministrativeArea.new_york.value.area_code,
                },
                'address_postcode': '91012',
                'address_country': 'US',
            },
        }

        dnb_response = {
            'id': '11111111-2222-3333-4444-555555555555',
            'status': 'pending',
            'created_on': '2020-01-05T11:00:00',
            **dnb_formatted_company_details,
        }

        requests_mock.post(
            DNB_INVESTIGATION_URL,
            status_code=status.HTTP_201_CREATED,
            json=dnb_response,
        )

        response = self.api_client.post(
            reverse('api-v4:dnb-api:company-investigation'),
            data={
                'company': company.id,
                'name': 'Joe Bloggs LTD',
                'website': 'https://www.example.com',
                'telephone_number': '123456789',
                'address': {
                    'line_1': '23 Code Street',
                    'line_2': 'Someplace',
                    'town': 'Beverly Hills',
                    'county': 'Los Angeles',
                    'area': {
                        'id': constants.AdministrativeArea.new_york.value.id,
                    },
                    'postcode': '91012',
                    'country': constants.Country.united_states.value.id,
                },
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == dnb_response
        assert requests_mock.last_request.json() == dnb_formatted_company_details
        company.refresh_from_db()
        assert str(company.dnb_investigation_id) == dnb_response['id']
        assert company.pending_dnb_investigation is True

    @pytest.mark.parametrize(
        ('missing_field_data_hub', 'missing_field_dnb_service'),
        [
            ('website', 'domain'),
            ('telephone_number', 'telephone_number'),
        ],
    )
    def test_valid_minimum_data(
        self,
        requests_mock,
        missing_field_data_hub,
        missing_field_dnb_service,
    ):
        """The endpoint should return 200 as well as a valid response when it is hit with a valid
        payload of the minimum required investigation details.
        """
        company = CompanyFactory()
        dnb_formatted_company_details = {
            'company_details': {
                'primary_name': 'Joe Bloggs LTD',
                'telephone_number': '123456789',
                'domain': 'joe.com',
                'address_line_1': '23 Code Street',
                'address_town': 'London',
                'address_country': 'GB',
            },
        }
        dnb_formatted_company_details['company_details'].pop(missing_field_dnb_service)
        dnb_response = {
            'id': '11111111-2222-3333-4444-555555555555',
            'status': 'pending',
            'created_on': '2020-01-05T11:00:00',
            **dnb_formatted_company_details,
        }

        requests_mock.post(
            DNB_INVESTIGATION_URL,
            status_code=status.HTTP_201_CREATED,
            json=dnb_response,
        )

        payload = {
            'company': company.id,
            'name': 'Joe Bloggs LTD',
            'telephone_number': '123456789',
            'website': 'https://joe.com',
            'address': {
                'line_1': '23 Code Street',
                'town': 'London',
                'country': constants.Country.united_kingdom.value.id,
            },
        }
        payload.pop(missing_field_data_hub)

        response = self.api_client.post(
            reverse('api-v4:dnb-api:company-investigation'),
            data=payload,
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == dnb_response
        assert requests_mock.last_request.json() == dnb_formatted_company_details
        company.refresh_from_db()
        assert str(company.dnb_investigation_id) == dnb_response['id']
        assert company.pending_dnb_investigation is True

    @pytest.mark.parametrize(
        'status_code',
        [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_405_METHOD_NOT_ALLOWED,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            status.HTTP_502_BAD_GATEWAY,
        ],
    )
    def test_dnb_service_error(
        self,
        requests_mock,
        status_code,
    ):
        """The  endpoint should return 502 if the upstream `dnb-service` returns an error."""
        company = CompanyFactory()
        requests_mock.post(
            DNB_INVESTIGATION_URL,
            status_code=status_code,
        )

        response = self.api_client.post(
            reverse('api-v4:dnb-api:company-investigation'),
            data={
                'company': company.id,
                'name': 'Joe Bloggs LTD',
                'website': 'https://www.example.com',
                'telephone_number': '123456789',
                'address': {
                    'line_1': '23 Code Street',
                    'line_2': 'Someplace',
                    'town': 'London',
                    'county': 'Greater London',
                    'postcode': 'W1 0TN',
                    'country': constants.Country.united_kingdom.value.id,
                },
            },
        )

        assert response.status_code == status.HTTP_502_BAD_GATEWAY

    @override_settings(DNB_SERVICE_BASE_URL=None)
    def test_post_no_dnb_setting(self):
        """Test that we get an ImproperlyConfigured exception when the DNB_SERVICE_BASE_URL setting
        is not set.
        """
        company = CompanyFactory()

        with pytest.raises(ImproperlyConfigured):
            self.api_client.post(
                reverse('api-v4:dnb-api:company-investigation'),
                data={
                    'company': company.id,
                    'name': 'Joe Bloggs LTD',
                    'website': 'https://www.example.com',
                    'telephone_number': '123456789',
                    'address': {
                        'line_1': '23 Code Street',
                        'line_2': 'Someplace',
                        'town': 'London',
                        'county': 'Greater London',
                        'postcode': 'W1 0TN',
                        'country': constants.Country.united_kingdom.value.id,
                    },
                },
            )

    @pytest.mark.parametrize(
        ('request_exception', 'expected_exception', 'expected_message'),
        [
            (
                ConnectionError,
                DNBServiceConnectionError,
                'Encountered an error connecting to DNB service',
            ),
            (
                Timeout,
                DNBServiceTimeoutError,
                'Encountered a timeout interacting with DNB service',
            ),
        ],
    )
    def test_request_error(
        self,
        requests_mock,
        request_exception,
        expected_exception,
        expected_message,
    ):
        """Test if there is an error connecting to dnb-service, we raise the
        exception with an appropriate message.
        """
        company = CompanyFactory()
        requests_mock.post(
            DNB_INVESTIGATION_URL,
            exc=request_exception,
        )

        response = self.api_client.post(
            reverse('api-v4:dnb-api:company-investigation'),
            data={
                'company': company.id,
                'name': 'Joe Bloggs LTD',
                'website': 'https://www.example.com',
                'telephone_number': '123456789',
                'address': {
                    'line_1': '23 Code Street',
                    'line_2': 'Someplace',
                    'town': 'London',
                    'county': 'Greater London',
                    'postcode': 'W1 0TN',
                    'country': constants.Country.united_kingdom.value.id,
                },
            },
        )
        assert response.status_code == status.HTTP_502_BAD_GATEWAY


class TestHierarchyAPITestMixin:
    def set_dnb_hierarchy_mock_response(self, requests_mock, tree_members, status_code=200):
        self.set_dnb_hierarchy_count_mock_response(requests_mock, len(tree_members), status_code)
        requests_mock.post(
            DNB_HIERARCHY_SEARCH_URL,
            status_code=status_code,
            content=json.dumps(
                {
                    'global_ultimate_duns': 'duns',
                    'family_tree_members': tree_members,
                    'global_ultimate_family_tree_members_count': len(tree_members),
                },
            ).encode('utf-8'),
        )

    def set_dnb_hierarchy_count_mock_response(self, requests_mock, count, status_code=200):
        requests_mock.post(
            DNB_HIERARCHY_COUNT_URL,
            status_code=status_code,
            content=str(count).encode(),
        )


class TestCompanyHierarchyView(APITestMixin, TestHierarchyAPITestMixin):
    """DNB Company Hierarchy Search view test case."""

    def test_company_id_is_valid(self):
        assert (
            self.api_client.get(
                reverse('api-v4:dnb-api:family-tree', kwargs={'company_id': '11223344'}),
            ).status_code
            == 400
        )

    def test_company_has_no_company_id(self):
        assert (
            self.api_client.get(
                reverse('api-v4:dnb-api:family-tree', kwargs={'company_id': uuid4()}),
            ).status_code
            == 404
        )

    def test_company_has_no_duns_number(self):
        company = CompanyFactory(duns_number=None)
        assert (
            self.api_client.get(
                reverse('api-v4:dnb-api:family-tree', kwargs={'company_id': company.id}),
            ).status_code
            == 400
        )

    def test_empty_results_from_dnb_and_no_has_manually_linked(
        self,
        requests_mock,
        opensearch_with_signals,
    ):
        """Test when a company has no dnb related companies and no manually linked an empty response
        is returned.
        """
        api_client = self.create_api_client()
        company = CompanyFactory(duns_number='123456789')

        opensearch_with_signals.indices.refresh()

        self.set_dnb_hierarchy_count_mock_response(requests_mock, 0)
        requests_mock.post(
            DNB_HIERARCHY_SEARCH_URL,
            json={'family_tree_members': []},
        )

        url = reverse('api-v4:dnb-api:family-tree', kwargs={'company_id': company.id})
        response = api_client.get(
            url,
            content_type='application/json',
        )

        assert response.status_code == 200
        assert response.json() == {
            'ultimate_global_company': {},
            'ultimate_global_companies_count': 0,
            'family_tree_companies_count': 0,
            'manually_verified_subsidiaries': [],
            'reduced_tree': False,
        }

    def test_empty_results_from_dnb_include_requested_company_when_company_has_manually_linked(
        self,
        requests_mock,
        opensearch_with_signals,
    ):
        """Test when empty results are returned from dnb but the company has manually linked
        subsidiaries the requested company is returned as the global ultimate of the tree.
        """
        api_client = self.create_api_client()
        company = CompanyFactory(duns_number='123456789')
        subsidiary_company = CompanyFactory(global_headquarters=company)

        opensearch_with_signals.indices.refresh()

        self.set_dnb_hierarchy_count_mock_response(requests_mock, 0)
        requests_mock.post(
            DNB_HIERARCHY_SEARCH_URL,
            json={'family_tree_members': []},
        )

        url = reverse('api-v4:dnb-api:family-tree', kwargs={'company_id': company.id})
        response = api_client.get(
            url,
            content_type='application/json',
        )

        assert response.status_code == 200
        assert response.json() == {
            'ultimate_global_company': {
                'duns_number': company.duns_number,
                'id': str(company.id),
                'name': company.name,
                'number_of_employees': company.number_of_employees,
                'address': {
                    'country': {
                        'id': str(company.address_country.id),
                        'name': company.address_country.name,
                    },
                    'county': '',
                    'line_1': company.address_1,
                    'line_2': '',
                    'postcode': company.address_postcode,
                    'town': company.address_town,
                },
                'registered_address': {
                    'country': {
                        'id': str(company.registered_address_country.id),
                        'name': company.registered_address_country.name,
                    },
                    'county': '',
                    'line_1': company.registered_address_1,
                    'line_2': '',
                    'postcode': company.registered_address_postcode,
                    'town': company.registered_address_town,
                },
                'sector': {
                    'id': str(company.sector.id),
                    'name': company.sector.name,
                },
                'trading_names': [],
                'headquarter_type': company.headquarter_type,
                'uk_region': {
                    'id': str(company.uk_region.id),
                    'name': company.uk_region.name,
                },
                'one_list_tier': None,
                'archived': False,
                'latest_interaction_date': None,
                'hierarchy': None,
                'is_out_of_business': None,
            },
            'ultimate_global_companies_count': 1,
            'family_tree_companies_count': 1,
            'manually_verified_subsidiaries': [
                {
                    'id': str(subsidiary_company.id),
                    'name': subsidiary_company.name,
                    'employee_range': {
                        'id': str(subsidiary_company.employee_range.id),
                        'name': subsidiary_company.employee_range.name,
                    },
                    'headquarter_type': None,
                    'uk_region': {
                        'id': str(subsidiary_company.uk_region.id),
                        'name': subsidiary_company.uk_region.name,
                    },
                    'archived': False,
                    'address': {
                        'line_1': subsidiary_company.address_1,
                        'line_2': '',
                        'town': subsidiary_company.address_town,
                        'county': '',
                        'postcode': subsidiary_company.address_postcode,
                        'area': None,
                        'country': {
                            'id': str(subsidiary_company.address_country.id),
                            'name': subsidiary_company.address_country.name,
                        },
                    },
                    'hierarchy': '0',
                    'one_list_tier': None,
                    'trading_names': subsidiary_company.trading_names,
                },
            ],
            'reduced_tree': False,
        }

    def test_dnb_response_with_a_duns_number_matching_dh_company_duns_number_appends_dh_id(
        self,
        requests_mock,
        opensearch_with_signals,
    ):
        """Test the scenario where the company returned by the DnB service does match a company found
        in the Data Hub dataset and then return the correct id for that company.
        """
        faker = Faker()

        trading_names = ['Trading name 1', 'Trading name 2']

        ultimate_company_dnb = {
            'duns': '987654321',
            'primaryName': faker.company(),
            'corporateLinkage': {'hierarchyLevel': 1},
            'tradeStyleNames': [
                {
                    'name': trading_names[0],
                    'priority': 1,
                },
                {
                    'name': trading_names[1],
                    'priority': 2,
                },
            ],
        }

        tree_members = [
            ultimate_company_dnb,
        ]

        ultimate_company_dh = CompanyFactory(
            duns_number=ultimate_company_dnb['duns'],
            id='8e2e9b35-3415-4b9b-b9ff-f97446ac8942',
            name=ultimate_company_dnb['primaryName'],
            one_list_tier=OneListTier.objects.first(),
        )
        opensearch_with_signals.indices.refresh()

        response = self._get_family_tree_response(requests_mock, tree_members, ultimate_company_dh)

        assert response.status_code == 200
        assert response.json() == {
            'ultimate_global_company': {
                'duns_number': ultimate_company_dnb['duns'],
                'id': ultimate_company_dh.id,
                'name': ultimate_company_dh.name,
                'number_of_employees': ultimate_company_dh.number_of_employees,
                'address': {
                    'country': {
                        'id': str(ultimate_company_dh.address_country.id),
                        'name': ultimate_company_dh.address_country.name,
                    },
                    'county': '',
                    'line_1': ultimate_company_dh.address_1,
                    'line_2': '',
                    'postcode': ultimate_company_dh.address_postcode,
                    'town': ultimate_company_dh.address_town,
                },
                'registered_address': {
                    'country': {
                        'id': str(ultimate_company_dh.registered_address_country.id),
                        'name': ultimate_company_dh.registered_address_country.name,
                    },
                    'county': '',
                    'line_1': ultimate_company_dh.registered_address_1,
                    'line_2': '',
                    'postcode': ultimate_company_dh.registered_address_postcode,
                    'town': ultimate_company_dh.registered_address_town,
                },
                'sector': {
                    'id': str(ultimate_company_dh.sector.id),
                    'name': ultimate_company_dh.sector.name,
                },
                'trading_names': trading_names,
                'headquarter_type': ultimate_company_dh.headquarter_type,
                'uk_region': {
                    'id': str(ultimate_company_dh.uk_region.id),
                    'name': ultimate_company_dh.uk_region.name,
                },
                'one_list_tier': {
                    'id': str(ultimate_company_dh.one_list_tier.id),
                    'name': ultimate_company_dh.one_list_tier.name,
                },
                'archived': False,
                'latest_interaction_date': None,
                'hierarchy': 1,
                'is_out_of_business': None,
            },
            'ultimate_global_companies_count': len(tree_members),
            'manually_verified_subsidiaries': [],
            'reduced_tree': False,
            'family_tree_companies_count': len(tree_members),
        }

    def test_dnb_response_with_only_ultimate_parent_matching_a_datahub_company(
        self,
        requests_mock,
        opensearch_with_signals,
    ):
        """Test the scenario where the ultimate parent is the only company in the response from the
        proxy service that matches a duns number in the datahub dataset.
        """
        faker = Faker()

        ultimate_tree_member_level_1 = {
            'duns': '987654321',
            'primaryName': faker.company(),
            'corporateLinkage': {'hierarchyLevel': 1},
            'numberOfEmployees': [{'value': 400}],
            'tradeStyleNames': [
                {
                    'name': 'Trading name 1',
                    'priority': 1,
                },
            ],
        }
        tree_member_level_2 = {
            'duns': '123456789',
            'primaryName': faker.company(),
            'corporateLinkage': {
                'hierarchyLevel': 2,
                'parent': {'duns': ultimate_tree_member_level_1['duns']},
            },
            'numberOfEmployees': [{'value': 150}],
        }
        tree_member_level_3 = {
            'duns': '777777777',
            'primaryName': faker.company(),
            'corporateLinkage': {
                'hierarchyLevel': 3,
                'parent': {'duns': tree_member_level_2['duns']},
            },
        }

        tree_members = [
            ultimate_tree_member_level_1,
            tree_member_level_2,
            tree_member_level_3,
        ]

        ultimate_company_dh = CompanyFactory(
            id='8e2e9b35-3415-4b9b-b9ff-f97446ac8942',
            duns_number=ultimate_tree_member_level_1['duns'],
            archived=True,
            number_of_employees=5000,
        )

        opensearch_with_signals.indices.refresh()

        response = self._get_family_tree_response(requests_mock, tree_members, ultimate_company_dh)
        assert response.status_code == 200
        assert response.json() == {
            'ultimate_global_company': {
                'duns_number': ultimate_tree_member_level_1['duns'],
                'name': ultimate_company_dh.name,
                'number_of_employees': 400,
                'id': ultimate_company_dh.id,
                'address': {
                    'country': {
                        'id': str(ultimate_company_dh.address_country.id),
                        'name': ultimate_company_dh.address_country.name,
                    },
                    'county': '',
                    'line_1': ultimate_company_dh.address_1,
                    'line_2': '',
                    'postcode': ultimate_company_dh.address_postcode,
                    'town': ultimate_company_dh.address_town,
                },
                'registered_address': {
                    'country': {
                        'id': str(ultimate_company_dh.registered_address_country.id),
                        'name': ultimate_company_dh.registered_address_country.name,
                    },
                    'county': '',
                    'line_1': ultimate_company_dh.registered_address_1,
                    'line_2': '',
                    'postcode': ultimate_company_dh.registered_address_postcode,
                    'town': ultimate_company_dh.registered_address_town,
                },
                'sector': {
                    'id': str(ultimate_company_dh.sector.id),
                    'name': ultimate_company_dh.sector.name,
                },
                'trading_names': [ultimate_tree_member_level_1.get('tradeStyleNames')[0]['name']],
                'headquarter_type': ultimate_company_dh.headquarter_type,
                'uk_region': {
                    'id': str(ultimate_company_dh.uk_region.id),
                    'name': ultimate_company_dh.uk_region.name,
                },
                'one_list_tier': None,
                'archived': True,
                'latest_interaction_date': None,
                'hierarchy': 1,
                'is_out_of_business': None,
                'subsidiaries': [
                    {
                        'duns_number': tree_member_level_2['duns'],
                        'id': None,
                        'name': tree_member_level_2['primaryName'],
                        'number_of_employees': tree_member_level_2['numberOfEmployees'][0][
                            'value'
                        ],
                        'address': None,
                        'registered_address': None,
                        'sector': None,
                        'trading_names': [],
                        'headquarter_type': None,
                        'uk_region': None,
                        'one_list_tier': None,
                        'archived': False,
                        'latest_interaction_date': None,
                        'hierarchy': 2,
                        'is_out_of_business': False,
                        'subsidiaries': [
                            {
                                'duns_number': tree_member_level_3['duns'],
                                'id': None,
                                'name': tree_member_level_3['primaryName'],
                                'number_of_employees': None,
                                'address': None,
                                'registered_address': None,
                                'sector': None,
                                'trading_names': [],
                                'headquarter_type': None,
                                'uk_region': None,
                                'one_list_tier': None,
                                'archived': False,
                                'latest_interaction_date': None,
                                'hierarchy': 3,
                                'is_out_of_business': False,
                            },
                        ],
                    },
                ],
            },
            'ultimate_global_companies_count': len(tree_members),
            'manually_verified_subsidiaries': [],
            'reduced_tree': False,
            'family_tree_companies_count': len(tree_members),
        }

    def _get_family_tree_response(
        self,
        requests_mock,
        tree_members,
        ultimate_company,
    ):
        api_client = self.create_api_client()
        self.set_dnb_hierarchy_mock_response(requests_mock, tree_members)

        url = reverse('api-v4:dnb-api:family-tree', kwargs={'company_id': ultimate_company.id})
        response = api_client.get(
            url,
            content_type='application/json',
        )

        return response

    @pytest.mark.parametrize(
        'request_exception',
        [(ConnectionError), (DNBServiceTimeoutError)],
    )
    def test_dnb_request_connection_error(self, requests_mock, request_exception):
        """Test dnb api request exceptopn."""
        api_client = self.create_api_client()
        company = CompanyFactory(duns_number='123456789')
        self.set_dnb_hierarchy_count_mock_response(requests_mock, 0)
        requests_mock.post(
            DNB_HIERARCHY_SEARCH_URL,
            exc=request_exception,
        )

        url = reverse('api-v4:dnb-api:family-tree', kwargs={'company_id': company.id})
        response = api_client.get(
            url,
            content_type='application/json',
        )

        assert response.status_code == status.HTTP_502_BAD_GATEWAY

    def _subsidiary_to_json(self, subsidiary):
        return {
            'id': str(subsidiary.id),
            'name': subsidiary.name,
            'employee_range': {
                'id': str(subsidiary.employee_range.id),
                'name': subsidiary.employee_range.name,
            },
            'headquarter_type': {
                'id': str(subsidiary.headquarter_type.id),
                'name': subsidiary.headquarter_type.name,
            },
            'address': {
                'line_1': subsidiary.address_1,
                'line_2': subsidiary.address_2,
                'town': subsidiary.address_town,
                'county': subsidiary.address_county,
                'postcode': subsidiary.address_postcode,
                'country': {
                    'id': str(subsidiary.address_country.id),
                    'name': subsidiary.address_country.name,
                },
                'area': {
                    'id': str(subsidiary.address_area.id),
                    'name': subsidiary.address_area.name,
                },
            },
            'uk_region': {
                'id': str(subsidiary.uk_region.id),
                'name': subsidiary.uk_region.name,
            },
            'one_list_tier': {
                'id': str(subsidiary.one_list_tier.id),
                'name': subsidiary.one_list_tier.name,
            },
            'archived': subsidiary.archived,
            'hierarchy': '0',
            'trading_names': subsidiary.trading_names,
        }

    def test_manually_verified_subsidiaries_empty(self, requests_mock, opensearch_with_signals):
        faker = Faker()

        ultimate_tree_member_level_1 = {
            'duns': '987654321',
            'primaryName': faker.company(),
            'corporateLinkage': {'hierarchyLevel': 1},
        }

        ultimate_company_dh = CompanyFactory(
            duns_number=ultimate_tree_member_level_1['duns'],
        )

        opensearch_with_signals.indices.refresh()

        response = self._get_family_tree_response(
            requests_mock,
            [ultimate_tree_member_level_1],
            ultimate_company_dh,
        )

        assert response.json()['manually_verified_subsidiaries'] == []

    def test_manually_verified_subsidiaries(self, requests_mock):
        faker = Faker()

        ultimate_tree_member_level_1 = {
            'duns': '987654321',
            'primaryName': faker.company(),
            'corporateLinkage': {'hierarchyLevel': 1},
        }

        ultimate_company_dh = CompanyFactory(
            duns_number=ultimate_tree_member_level_1['duns'],
        )
        subsidiary = CompanyFactory(
            global_headquarters_id=ultimate_company_dh.id,
            headquarter_type_id=constants.HeadquarterType.ghq.value.id,
            address_area_id=constants.AdministrativeArea.texas.value.id,
            one_list_tier_id=OneListTierID.tier_d_international_trade_advisers.value,
        )

        response = self._get_family_tree_response(
            requests_mock,
            [ultimate_tree_member_level_1],
            ultimate_company_dh,
        )
        assert response.json()['manually_verified_subsidiaries'] == [
            self._subsidiary_to_json(subsidiary),
        ]

    def test_manually_verified_subsidiaries_included_when_no_dnb_companies_found(
        self,
        requests_mock,
    ):
        ultimate_company_dh = CompanyFactory(duns_number='987654321')
        subsidiary = CompanyFactory(
            global_headquarters_id=ultimate_company_dh.id,
            headquarter_type_id=constants.HeadquarterType.ghq.value.id,
            address_area_id=constants.AdministrativeArea.texas.value.id,
            one_list_tier_id=OneListTierID.tier_d_international_trade_advisers.value,
        )

        response = self._get_family_tree_response(
            requests_mock,
            [],
            ultimate_company_dh,
        )
        assert response.json()['manually_verified_subsidiaries'] == [
            self._subsidiary_to_json(subsidiary),
        ]

    def test_multiple_manually_verified_subsidiaries(self, requests_mock, opensearch_with_signals):
        faker = Faker()

        ultimate_tree_member_level_1 = {
            'duns': '987654321',
            'primaryName': faker.company(),
            'corporateLinkage': {'hierarchyLevel': 1},
        }

        ultimate_company_dh = CompanyFactory(
            duns_number=ultimate_tree_member_level_1['duns'],
        )
        first_subsidiary = CompanyFactory(
            name='First Subsidiary',
            global_headquarters_id=ultimate_company_dh.id,
            headquarter_type_id=constants.HeadquarterType.ghq.value.id,
            address_area_id=constants.AdministrativeArea.texas.value.id,
            one_list_tier_id=OneListTierID.tier_d_international_trade_advisers.value,
        )
        second_subsidiary = CompanyFactory(
            name='Second Subsidiary',
            global_headquarters_id=ultimate_company_dh.id,
            headquarter_type_id=constants.HeadquarterType.ghq.value.id,
            address_area_id=constants.AdministrativeArea.texas.value.id,
            one_list_tier_id=OneListTierID.tier_d_international_trade_advisers.value,
        )

        opensearch_with_signals.indices.refresh()

        response = self._get_family_tree_response(
            requests_mock,
            [ultimate_tree_member_level_1],
            ultimate_company_dh,
        )

        response.json()['manually_verified_subsidiaries'].sort(
            key=operator.itemgetter('name'),
        )

        assert response.json()['manually_verified_subsidiaries'] == [
            self._subsidiary_to_json(first_subsidiary),
            self._subsidiary_to_json(second_subsidiary),
        ]

    def test_more_than_maximum_allowed_companies_returns_reduced_tree(
        self,
        opensearch_with_signals,
    ):
        """Test the scenario where the count of companies returned by the dnb service is above the
        maximum allowed, so a reduced company tree is returned instead.
        """
        faker = Faker()

        ultimate_company_dnb = {
            'duns': '111111111',
            'primaryName': faker.company(),
            'corporateLinkage': {'hierarchyLevel': 1},
        }
        tree_members = [
            {
                'duns': '222222222',
                'primaryName': faker.company(),
                'corporateLinkage': {'hierarchyLevel': 2, 'parent': '111111111'},
            }
            for x in range(1001)
        ]
        tree_members.insert(0, ultimate_company_dnb)

        ultimate_company_dh = CompanyFactory(
            duns_number=ultimate_company_dnb['duns'],
            id='8e2e9b35-3415-4b9b-b9ff-f97446ac8942',
            name=ultimate_company_dnb['primaryName'],
            one_list_tier=OneListTier.objects.first(),
        )
        opensearch_with_signals.indices.refresh()
        with requests_mock.Mocker() as m:
            m.post(
                DNB_V2_SEARCH_URL,
                [
                    {
                        'json': {
                            'results': [{'duns_number': '111111111'}],
                        },
                    },
                    {
                        'json': {
                            'results': [
                                {'duns_number': '222222222', 'parent_duns_number': '111111111'},
                            ],
                        },
                    },
                ],
            )

            response = self._get_family_tree_response(
                m,
                tree_members,
                ultimate_company_dh,
            )

            assert response.status_code == 200
            assert response.json()['reduced_tree'] is True

    @patch(
        'datahub.dnb_api.views.validate_company_id',
    )
    @pytest.mark.usefixtures('local_memory_cache')
    def test_view_is_cached(
        self,
        validate_company_id_mock,
        requests_mock,
        opensearch_with_signals,
    ):
        """Call the endpoint multiple times, and ensure only the first gets through the django
        caching layer.
        """
        faker = Faker()

        ultimate_company_dnb = {
            'duns': '987654321',
            'primaryName': faker.company(),
            'corporateLinkage': {'hierarchyLevel': 1},
        }

        tree_members = [
            ultimate_company_dnb,
        ]

        ultimate_company_dh = CompanyFactory(
            duns_number=ultimate_company_dnb['duns'],
            id=uuid4(),
            name=ultimate_company_dnb['primaryName'],
            one_list_tier=OneListTier.objects.first(),
        )
        opensearch_with_signals.indices.refresh()

        validate_company_id_mock.return_value = ultimate_company_dnb['duns']

        for _ in range(3):
            self._get_family_tree_response(requests_mock, tree_members, ultimate_company_dh)

        assert validate_company_id_mock.call_count == 1


class TestRelatedCompanyView(APITestMixin, TestHierarchyAPITestMixin):
    """DNB Company Hierarchy Search view test case."""

    def test_company_id_is_valid(self):
        api_client = self.create_api_client()
        company = CompanyFactory(duns_number='12345678')

        url = reverse('api-v4:dnb-api:related-companies', kwargs={'company_id': company.id})
        response = api_client.get(
            f'{url}{URL_PARENT_TRUE_SUBSIDIARY_TRUE}',
            content_type='application/json',
        )
        assert response.status_code == 400

    def test_company_has_no_company_id(self):
        api_client = self.create_api_client()
        url = reverse('api-v4:dnb-api:related-companies', kwargs={'company_id': uuid4()})
        response = api_client.get(
            f'{url}{URL_PARENT_TRUE_SUBSIDIARY_TRUE}',
            content_type='application/json',
        )
        assert response.status_code == 404

    def test_company_has_no_duns_number(self):
        api_client = self.create_api_client()
        company = CompanyFactory(duns_number=None)

        url = reverse('api-v4:dnb-api:related-companies', kwargs={'company_id': company.id})
        response = api_client.get(
            f'{url}{URL_PARENT_TRUE_SUBSIDIARY_TRUE}',
            content_type='application/json',
        )
        assert response.status_code == 400

    @patch(
        'datahub.dnb_api.views.get_datahub_ids_for_dnb_service_company_hierarchy',
    )
    @pytest.mark.parametrize(
        'request_exception',
        [(ConnectionError), (DNBServiceTimeoutError)],
    )
    def test_related_companies_request_connection_error(
        self,
        get_datahub_ids_for_dnb_service_company_hierarchy_mock,
        requests_mock,
        request_exception,
    ):
        """Test for POST proxy."""
        api_client = self.create_api_client()
        company = CompanyFactory(duns_number='123456789')
        requests_mock.post(
            DNB_HIERARCHY_SEARCH_URL,
            exc=request_exception,
        )
        self.set_dnb_hierarchy_count_mock_response(requests_mock, 2)

        get_datahub_ids_for_dnb_service_company_hierarchy_mock.side_effect = APIUpstreamException(
            'exc',
        )

        url = reverse('api-v4:dnb-api:related-companies', kwargs={'company_id': company.id})
        response = api_client.get(
            f'{url}{URL_PARENT_TRUE_SUBSIDIARY_TRUE}',
            content_type='application/json',
        )

        assert response.status_code == status.HTTP_502_BAD_GATEWAY

    def test_empty_results_returned_from_dnb_service(self, requests_mock):
        """Test for POST proxy."""
        api_client = self.create_api_client()
        company = CompanyFactory(duns_number='123456789')

        requests_mock.post(
            DNB_HIERARCHY_SEARCH_URL,
            status_code=200,
            json={'family_tree_members': None},
        )
        self.set_dnb_hierarchy_count_mock_response(requests_mock, 2)

        url = reverse('api-v4:dnb-api:related-companies', kwargs={'company_id': company.id})
        response = api_client.get(
            f'{url}{URL_PARENT_TRUE_SUBSIDIARY_TRUE}',
            content_type='application/json',
        )

        assert response.status_code == 200

        assert response.json() == {
            'related_companies': [],
            'reduced_tree': None,
        }

    def test_single_subsidiary_id_is_returned_when_exists_in_data_hub(
        self,
        requests_mock,
        opensearch_with_signals,
    ):
        """Test the scenario where the company returned by the DnB service does
        match a child company found in the Data Hub dataset and then return
        the correct id for that company.
        """
        faker = Faker()
        ultimate_company_dnb = {
            'duns': '987654321',
            'primaryName': faker.company(),
            'corporateLinkage': {'hierarchyLevel': 1},
        }

        child_company_dnb = {
            'duns': '123456789',
            'primaryName': faker.company(),
            'corporateLinkage': {
                'hierarchyLevel': 2,
                'parent': {'duns': ultimate_company_dnb['duns']},
            },
        }

        tree_members = [ultimate_company_dnb, child_company_dnb]
        ultimate_company_dh = CompanyFactory(
            duns_number=ultimate_company_dnb['duns'],
            id='8e2e9b35-3415-4b9b-b9ff-f97446ac8942',
            name=ultimate_company_dnb['primaryName'],
        )
        child_company_dh = CompanyFactory(
            duns_number=child_company_dnb['duns'],
            id='111e9b35-3415-4b9b-b9ff-f97446ac8942',
            name=child_company_dnb['primaryName'],
        )

        opensearch_with_signals.indices.refresh()

        params = URL_PARENT_TRUE_SUBSIDIARY_TRUE

        response = self._get_related_company_response(
            requests_mock,
            tree_members,
            ultimate_company_dh,
            params,
        )

        assert response.status_code == 200
        assert response.json() == {
            'related_companies': [child_company_dh.id],
            'reduced_tree': False,
        }

    def test_single_parent_id_is_returned_when_exists_in_data_hub(
        self,
        requests_mock,
        opensearch_with_signals,
    ):
        """Test the scenario where the company returned by the DnB service does
        match a parent company found in the Data Hub dataset and then return
        the correct id for that company.
        """
        faker = Faker()

        ultimate_company_dnb = {
            'duns': '987654321',
            'primaryName': faker.company(),
            'corporateLinkage': {'hierarchyLevel': 1},
        }

        child_company_dnb = {
            'duns': '123456789',
            'primaryName': faker.company(),
            'corporateLinkage': {
                'hierarchyLevel': 2,
                'parent': {'duns': ultimate_company_dnb['duns']},
            },
        }
        tree_members = [ultimate_company_dnb, child_company_dnb]
        ultimate_company_dh = CompanyFactory(
            duns_number=ultimate_company_dnb['duns'],
            id='8e2e9b35-3415-4b9b-b9ff-f97446ac8942',
            name=ultimate_company_dnb['primaryName'],
        )
        child_company_dh = CompanyFactory(
            duns_number=child_company_dnb['duns'],
            id='111e9b35-3415-4b9b-b9ff-f97446ac8942',
            name=child_company_dnb['primaryName'],
        )

        opensearch_with_signals.indices.refresh()

        params = URL_PARENT_TRUE_SUBSIDIARY_TRUE

        response = self._get_related_company_response(
            requests_mock,
            tree_members,
            child_company_dh,
            params,
        )

        assert response.status_code == 200
        assert response.json() == {
            'related_companies': [
                ultimate_company_dh.id,
            ],
            'reduced_tree': False,
        }

    def test_all_ids_except_self_are_returned_when_all_companies_are_in_data_hub_and_params_true(
        self,
        requests_mock,
        opensearch_with_signals,
    ):
        """Test the scenario where the companies returned by the DnB service all have
        Data Hub ids.
        """
        faker = Faker()

        ultimate_company_dnb = {
            'duns': '113456789',
            'primaryName': faker.company(),
            'corporateLinkage': {'hierarchyLevel': 1},
        }

        direct_company_dnb = {
            'duns': '223456789',
            'primaryName': faker.company(),
            'corporateLinkage': {
                'hierarchyLevel': 2,
                'parent': {'duns': ultimate_company_dnb['duns']},
            },
        }
        target_company_dnb = {
            'duns': '333456789',
            'primaryName': faker.company(),
            'corporateLinkage': {
                'hierarchyLevel': 4,
                'parent': {'duns': direct_company_dnb['duns']},
            },
        }
        child_one_company_dnb = {
            'duns': '443456789',
            'primaryName': faker.company(),
            'corporateLinkage': {
                'hierarchyLevel': 4,
                'parent': {'duns': target_company_dnb['duns']},
            },
        }
        child_two_company_dnb = {
            'duns': '553456789',
            'primaryName': faker.company(),
            'corporateLinkage': {
                'hierarchyLevel': 4,
                'parent': {'duns': target_company_dnb['duns']},
            },
        }
        tree_members = [
            ultimate_company_dnb,
            direct_company_dnb,
            target_company_dnb,
            child_one_company_dnb,
            child_two_company_dnb,
        ]
        ultimate_company_dh = CompanyFactory(
            duns_number=ultimate_company_dnb['duns'],
            id='111e9b35-3415-4b9b-b9ff-f97446ac8942',
            name=ultimate_company_dnb['primaryName'],
        )
        direct_company_dh = CompanyFactory(
            duns_number=direct_company_dnb['duns'],
            id='222e9b35-3415-4b9b-b9ff-f97446ac8942',
            name=direct_company_dnb['primaryName'],
        )
        target_company_dh = CompanyFactory(
            duns_number=target_company_dnb['duns'],
            id='333e9b35-3415-4b9b-b9ff-f97446ac8942',
            name=target_company_dnb['primaryName'],
        )
        child_one_company_dh = CompanyFactory(
            duns_number=child_one_company_dnb['duns'],
            id='444e9b35-3415-4b9b-b9ff-f97446ac8942',
            name=child_one_company_dnb['primaryName'],
        )
        child_two_company_dh = CompanyFactory(
            duns_number=child_two_company_dnb['duns'],
            id='555e9b35-3415-4b9b-b9ff-f97446ac8942',
            name=child_two_company_dnb['primaryName'],
        )

        opensearch_with_signals.indices.refresh()

        params = URL_PARENT_TRUE_SUBSIDIARY_TRUE

        response = self._get_related_company_response(
            requests_mock,
            tree_members,
            target_company_dh,
            params,
        )

        assert response.status_code == 200

        assert response.json() == {
            'related_companies': [
                ultimate_company_dh.id,
                direct_company_dh.id,
                child_one_company_dh.id,
                child_two_company_dh.id,
            ],
            'reduced_tree': False,
        }

    def test_only_ids_are_returned_when_companies_are_in_data_hub_and_params_true(
        self,
        requests_mock,
        opensearch_with_signals,
    ):
        """Test the scenario where not all the companies returned by the DnB service have
        a Data Hub id so only those that do should have their ID returned.
        """
        faker = Faker()

        ultimate_company_dnb = {
            'duns': '113456789',
            'primaryName': faker.company(),
            'corporateLinkage': {'hierarchyLevel': 1},
        }

        direct_company_dnb = {
            'duns': '223456789',
            'primaryName': faker.company(),
            'corporateLinkage': {
                'hierarchyLevel': 2,
                'parent': {'duns': ultimate_company_dnb['duns']},
            },
        }
        target_company_dnb = {
            'duns': '333456789',
            'primaryName': faker.company(),
            'corporateLinkage': {
                'hierarchyLevel': 4,
                'parent': {'duns': direct_company_dnb['duns']},
            },
        }
        child_one_company_dnb = {
            'duns': '443456789',
            'primaryName': faker.company(),
            'corporateLinkage': {
                'hierarchyLevel': 4,
                'parent': {'duns': target_company_dnb['duns']},
            },
        }
        child_two_company_dnb = {
            'duns': '553456789',
            'primaryName': faker.company(),
            'corporateLinkage': {
                'hierarchyLevel': 4,
                'parent': {'duns': target_company_dnb['duns']},
            },
        }
        tree_members = [
            ultimate_company_dnb,
            direct_company_dnb,
            target_company_dnb,
            child_one_company_dnb,
            child_two_company_dnb,
        ]
        ultimate_company_dh = CompanyFactory(
            duns_number=ultimate_company_dnb['duns'],
            id='111e9b35-3415-4b9b-b9ff-f97446ac8942',
            name=ultimate_company_dnb['primaryName'],
        )
        target_company_dh = CompanyFactory(
            duns_number=target_company_dnb['duns'],
            id='333e9b35-3415-4b9b-b9ff-f97446ac8942',
            name=target_company_dnb['primaryName'],
        )
        child_two_company_dh = CompanyFactory(
            duns_number=child_two_company_dnb['duns'],
            id='555e9b35-3415-4b9b-b9ff-f97446ac8942',
            name=child_two_company_dnb['primaryName'],
        )

        opensearch_with_signals.indices.refresh()

        params = URL_PARENT_TRUE_SUBSIDIARY_TRUE

        response = self._get_related_company_response(
            requests_mock,
            tree_members,
            target_company_dh,
            params,
        )

        assert response.status_code == 200

        assert response.json() == {
            'related_companies': [ultimate_company_dh.id, child_two_company_dh.id],
            'reduced_tree': False,
        }

    def test_no_ids_are_returned_when_no_companies_are_in_data_hub_and_params_true(
        self,
        requests_mock,
        opensearch_with_signals,
    ):
        """Test the scenario where the no companies returned by the DnB service have
        IDs in a Data Hub.
        """
        faker = Faker()

        ultimate_company_dnb = {
            'duns': '113456789',
            'primaryName': faker.company(),
            'corporateLinkage': {'hierarchyLevel': 1},
        }

        direct_company_dnb = {
            'duns': '223456789',
            'primaryName': faker.company(),
            'corporateLinkage': {
                'hierarchyLevel': 2,
                'parent': {'duns': ultimate_company_dnb['duns']},
            },
        }
        target_company_dnb = {
            'duns': '333456789',
            'primaryName': faker.company(),
            'corporateLinkage': {
                'hierarchyLevel': 4,
                'parent': {'duns': direct_company_dnb['duns']},
            },
        }
        child_one_company_dnb = {
            'duns': '443456789',
            'primaryName': faker.company(),
            'corporateLinkage': {
                'hierarchyLevel': 4,
                'parent': {'duns': target_company_dnb['duns']},
            },
        }
        child_two_company_dnb = {
            'duns': '553456789',
            'primaryName': faker.company(),
            'corporateLinkage': {
                'hierarchyLevel': 4,
                'parent': {'duns': target_company_dnb['duns']},
            },
        }
        tree_members = [
            ultimate_company_dnb,
            direct_company_dnb,
            target_company_dnb,
            child_one_company_dnb,
            child_two_company_dnb,
        ]
        target_company_dh = CompanyFactory(
            duns_number=target_company_dnb['duns'],
            id='333e9b35-3415-4b9b-b9ff-f97446ac8942',
            name=target_company_dnb['primaryName'],
        )

        opensearch_with_signals.indices.refresh()

        params = URL_PARENT_TRUE_SUBSIDIARY_TRUE

        response = self._get_related_company_response(
            requests_mock,
            tree_members,
            target_company_dh,
            params,
        )

        assert response.status_code == 200

        assert response.json() == {
            'related_companies': [],
            'reduced_tree': False,
        }

    def test_all_ids_directly_related_returned_when_all_companies_are_in_data_hub_and_params_true(
        self,
        requests_mock,
        opensearch_with_signals,
    ):
        """Test the scenario where the many companies returned by the DnB service does match
        for companies IDs in Data Hub but only those directly related are returned.
        """
        faker = Faker()

        ultimate_company_dnb = {
            'duns': '113456789',
            'primaryName': faker.company(),
            'corporateLinkage': {'hierarchyLevel': 1},
        }
        direct_company_dnb = {
            'duns': '223456789',
            'primaryName': faker.company(),
            'corporateLinkage': {
                'hierarchyLevel': 2,
                'parent': {'duns': ultimate_company_dnb['duns']},
            },
        }
        target_company_dnb = {
            'duns': '333456789',
            'primaryName': faker.company(),
            'corporateLinkage': {
                'hierarchyLevel': 3,
                'parent': {'duns': direct_company_dnb['duns']},
            },
        }
        child_one_company_dnb = {
            'duns': '443456789',
            'primaryName': faker.company(),
            'corporateLinkage': {
                'hierarchyLevel': 4,
                'parent': {'duns': target_company_dnb['duns']},
            },
        }
        not_directly_related_company_dnb = {
            'duns': '553456789',
            'primaryName': faker.company(),
            'corporateLinkage': {
                'hierarchyLevel': 2,
                'parent': {'duns': ultimate_company_dnb['duns']},
            },
        }
        tree_members = [
            ultimate_company_dnb,
            direct_company_dnb,
            target_company_dnb,
            child_one_company_dnb,
            not_directly_related_company_dnb,
        ]
        ultimate_company_dh = CompanyFactory(
            duns_number=ultimate_company_dnb['duns'],
            id='111e9b35-3415-4b9b-b9ff-f97446ac8942',
            name=ultimate_company_dnb['primaryName'],
        )
        direct_company_dh = CompanyFactory(
            duns_number=direct_company_dnb['duns'],
            id='222e9b35-3415-4b9b-b9ff-f97446ac8942',
            name=direct_company_dnb['primaryName'],
        )
        target_company_dh = CompanyFactory(
            duns_number=target_company_dnb['duns'],
            id='333e9b35-3415-4b9b-b9ff-f97446ac8942',
            name=target_company_dnb['primaryName'],
        )
        child_one_company_dh = CompanyFactory(
            duns_number=child_one_company_dnb['duns'],
            id='444e9b35-3415-4b9b-b9ff-f97446ac8942',
            name=child_one_company_dnb['primaryName'],
        )
        CompanyFactory(
            duns_number=not_directly_related_company_dnb['duns'],
            id='555e9b35-3415-4b9b-b9ff-f97446ac8942',
            name=not_directly_related_company_dnb['primaryName'],
        )  # not_directly_related_company_dh

        opensearch_with_signals.indices.refresh()

        params = URL_PARENT_TRUE_SUBSIDIARY_TRUE

        response = self._get_related_company_response(
            requests_mock,
            tree_members,
            target_company_dh,
            params,
        )

        assert response.status_code == 200

        assert response.json() == {
            'related_companies': [
                ultimate_company_dh.id,
                direct_company_dh.id,
                child_one_company_dh.id,
            ],
            'reduced_tree': False,
        }

    def test_only_parent_ids_returned_when_include_parent_set_true_and_include_subsidiary_false(
        self,
        requests_mock,
        opensearch_with_signals,
    ):
        """Test the scenario where the companies returned by the DnB service all have
        Data Hub ids.
        """
        faker = Faker()

        ultimate_company_dnb = {
            'duns': '113456789',
            'primaryName': faker.company(),
            'corporateLinkage': {'hierarchyLevel': 1},
        }

        direct_company_dnb = {
            'duns': '223456789',
            'primaryName': faker.company(),
            'corporateLinkage': {
                'hierarchyLevel': 2,
                'parent': {'duns': ultimate_company_dnb['duns']},
            },
        }
        target_company_dnb = {
            'duns': '333456789',
            'primaryName': faker.company(),
            'corporateLinkage': {
                'hierarchyLevel': 4,
                'parent': {'duns': direct_company_dnb['duns']},
            },
        }
        child_one_company_dnb = {
            'duns': '443456789',
            'primaryName': faker.company(),
            'corporateLinkage': {
                'hierarchyLevel': 4,
                'parent': {'duns': target_company_dnb['duns']},
            },
        }
        child_two_company_dnb = {
            'duns': '553456789',
            'primaryName': faker.company(),
            'corporateLinkage': {
                'hierarchyLevel': 4,
                'parent': {'duns': target_company_dnb['duns']},
            },
        }
        tree_members = [
            ultimate_company_dnb,
            direct_company_dnb,
            target_company_dnb,
            child_one_company_dnb,
            child_two_company_dnb,
        ]
        ultimate_company_dh = CompanyFactory(
            duns_number=ultimate_company_dnb['duns'],
            id='111e9b35-3415-4b9b-b9ff-f97446ac8942',
            name=ultimate_company_dnb['primaryName'],
        )
        direct_company_dh = CompanyFactory(
            duns_number=direct_company_dnb['duns'],
            id='222e9b35-3415-4b9b-b9ff-f97446ac8942',
            name=direct_company_dnb['primaryName'],
        )
        target_company_dh = CompanyFactory(
            duns_number=target_company_dnb['duns'],
            id='333e9b35-3415-4b9b-b9ff-f97446ac8942',
            name=target_company_dnb['primaryName'],
        )
        CompanyFactory(
            duns_number=child_one_company_dnb['duns'],
            id='444e9b35-3415-4b9b-b9ff-f97446ac8942',
            name=child_one_company_dnb['primaryName'],
        )  # child_one_company_dh
        CompanyFactory(
            duns_number=child_two_company_dnb['duns'],
            id='555e9b35-3415-4b9b-b9ff-f97446ac8942',
            name=child_two_company_dnb['primaryName'],
        )  # child_two_company_dh

        opensearch_with_signals.indices.refresh()

        params = URL_PARENT_TRUE_SUBSIDIARY_FALSE

        response = self._get_related_company_response(
            requests_mock,
            tree_members,
            target_company_dh,
            params,
        )

        assert response.status_code == 200

        assert response.json() == {
            'related_companies': [ultimate_company_dh.id, direct_company_dh.id],
            'reduced_tree': False,
        }

    def test_only_subsidiary_ids_returned_when_include_parent_false_and_include_subsidiary_true(
        self,
        requests_mock,
        opensearch_with_signals,
    ):
        """Test the scenario where the companies returned by the DnB service all have
        Data Hub ids.
        """
        faker = Faker()

        ultimate_company_dnb = {
            'duns': '113456789',
            'primaryName': faker.company(),
            'corporateLinkage': {'hierarchyLevel': 1},
        }

        direct_company_dnb = {
            'duns': '223456789',
            'primaryName': faker.company(),
            'corporateLinkage': {
                'hierarchyLevel': 2,
                'parent': {'duns': ultimate_company_dnb['duns']},
            },
        }
        target_company_dnb = {
            'duns': '333456789',
            'primaryName': faker.company(),
            'corporateLinkage': {
                'hierarchyLevel': 4,
                'parent': {'duns': direct_company_dnb['duns']},
            },
        }
        child_one_company_dnb = {
            'duns': '443456789',
            'primaryName': faker.company(),
            'corporateLinkage': {
                'hierarchyLevel': 4,
                'parent': {'duns': target_company_dnb['duns']},
            },
        }
        child_two_company_dnb = {
            'duns': '553456789',
            'primaryName': faker.company(),
            'corporateLinkage': {
                'hierarchyLevel': 4,
                'parent': {'duns': target_company_dnb['duns']},
            },
        }
        tree_members = [
            ultimate_company_dnb,
            direct_company_dnb,
            target_company_dnb,
            child_one_company_dnb,
            child_two_company_dnb,
        ]
        CompanyFactory(
            duns_number=ultimate_company_dnb['duns'],
            id='111e9b35-3415-4b9b-b9ff-f97446ac8942',
            name=ultimate_company_dnb['primaryName'],
        )  # ultimate_company_dh
        CompanyFactory(
            duns_number=direct_company_dnb['duns'],
            id='222e9b35-3415-4b9b-b9ff-f97446ac8942',
            name=direct_company_dnb['primaryName'],
        )  # direct_company_dh
        target_company_dh = CompanyFactory(
            duns_number=target_company_dnb['duns'],
            id='333e9b35-3415-4b9b-b9ff-f97446ac8942',
            name=target_company_dnb['primaryName'],
        )
        child_one_company_dh = CompanyFactory(
            duns_number=child_one_company_dnb['duns'],
            id='444e9b35-3415-4b9b-b9ff-f97446ac8942',
            name=child_one_company_dnb['primaryName'],
        )
        child_two_company_dh = CompanyFactory(
            duns_number=child_two_company_dnb['duns'],
            id='555e9b35-3415-4b9b-b9ff-f97446ac8942',
            name=child_two_company_dnb['primaryName'],
        )

        opensearch_with_signals.indices.refresh()

        prams = URL_PARENT_FALSE_SUBSIDIARY_TRUE

        response = self._get_related_company_response(
            requests_mock,
            tree_members,
            target_company_dh,
            prams,
        )

        assert response.status_code == 200
        assert response.json() == {
            'related_companies': [child_one_company_dh.id, child_two_company_dh.id],
            'reduced_tree': False,
        }

    def test_no_ids_returned_when_include_parent_false_and_include_subsidiary_false(
        self,
        requests_mock,
        opensearch_with_signals,
    ):
        """Test the scenario where the companies returned by the DnB service all have
        Data Hub ids.
        """
        faker = Faker()

        ultimate_company_dnb = {
            'duns': '113456789',
            'primaryName': faker.company(),
            'corporateLinkage': {'hierarchyLevel': 1},
        }

        direct_company_dnb = {
            'duns': '223456789',
            'primaryName': faker.company(),
            'corporateLinkage': {
                'hierarchyLevel': 2,
                'parent': {'duns': ultimate_company_dnb['duns']},
            },
        }
        target_company_dnb = {
            'duns': '333456789',
            'primaryName': faker.company(),
            'corporateLinkage': {
                'hierarchyLevel': 4,
                'parent': {'duns': direct_company_dnb['duns']},
            },
        }
        child_one_company_dnb = {
            'duns': '443456789',
            'primaryName': faker.company(),
            'corporateLinkage': {
                'hierarchyLevel': 4,
                'parent': {'duns': target_company_dnb['duns']},
            },
        }
        child_two_company_dnb = {
            'duns': '553456789',
            'primaryName': faker.company(),
            'corporateLinkage': {
                'hierarchyLevel': 4,
                'parent': {'duns': target_company_dnb['duns']},
            },
        }
        tree_members = [
            ultimate_company_dnb,
            direct_company_dnb,
            target_company_dnb,
            child_one_company_dnb,
            child_two_company_dnb,
        ]
        CompanyFactory(
            duns_number=ultimate_company_dnb['duns'],
            id='111e9b35-3415-4b9b-b9ff-f97446ac8942',
            name=ultimate_company_dnb['primaryName'],
        )
        CompanyFactory(
            duns_number=direct_company_dnb['duns'],
            id='222e9b35-3415-4b9b-b9ff-f97446ac8942',
            name=direct_company_dnb['primaryName'],
        )
        target_company_dh = CompanyFactory(
            duns_number=target_company_dnb['duns'],
            id='333e9b35-3415-4b9b-b9ff-f97446ac8942',
            name=target_company_dnb['primaryName'],
        )
        CompanyFactory(
            duns_number=child_one_company_dnb['duns'],
            id='444e9b35-3415-4b9b-b9ff-f97446ac8942',
            name=child_one_company_dnb['primaryName'],
        )
        CompanyFactory(
            duns_number=child_two_company_dnb['duns'],
            id='555e9b35-3415-4b9b-b9ff-f97446ac8942',
            name=child_two_company_dnb['primaryName'],
        )

        opensearch_with_signals.indices.refresh()

        params = URL_PARENT_FALSE_SUBSIDIARY_FALSE

        response = self._get_related_company_response(
            requests_mock,
            tree_members,
            target_company_dh,
            params,
        )

        assert response.status_code == 200
        assert response.json() == {'related_companies': [], 'reduced_tree': None}

    def _get_related_company_response(
        self,
        requests_mock,
        tree_members,
        ultimate_company,
        params,
    ):
        api_client = self.create_api_client()
        requests_mock.post(
            DNB_HIERARCHY_SEARCH_URL,
            status_code=200,
            content=json.dumps(
                {
                    'global_ultimate_duns': 'duns',
                    'family_tree_members': tree_members,
                    'global_ultimate_family_tree_members_count': len(tree_members),
                },
            ).encode('utf-8'),
        )
        self.set_dnb_hierarchy_count_mock_response(requests_mock, len(tree_members))
        url = reverse(
            'api-v4:dnb-api:related-companies',
            kwargs={'company_id': ultimate_company.id},
        )
        response = api_client.get(
            f'{url}{params}',
            content_type='application/json',
        )

        return response

    @patch(
        'datahub.dnb_api.utils.validate_company_id',
    )
    @pytest.mark.usefixtures('local_memory_cache')
    @pytest.mark.parametrize(
        'query_param',
        [
            URL_PARENT_TRUE_SUBSIDIARY_TRUE,
            URL_PARENT_TRUE_SUBSIDIARY_FALSE,
            URL_PARENT_FALSE_SUBSIDIARY_FALSE,
            URL_PARENT_FALSE_SUBSIDIARY_TRUE,
        ],
    )
    def test_view_is_cached(
        self,
        validate_company_id_mock,
        requests_mock,
        opensearch_with_signals,
        query_param,
    ):
        """Call the endpoint multiple times with different query params, and ensure only the first
        gets through the django caching layer.
        """
        faker = Faker()

        ultimate_company_dnb = {
            'duns': '113456789',
            'primaryName': faker.company(),
            'corporateLinkage': {'hierarchyLevel': 1},
        }

        tree_members = [
            ultimate_company_dnb,
        ]

        target_company_dh = CompanyFactory(
            duns_number=ultimate_company_dnb['duns'],
            id=uuid4(),
            name=ultimate_company_dnb['primaryName'],
        )

        opensearch_with_signals.indices.refresh()

        validate_company_id_mock.return_value = ultimate_company_dnb['duns']

        for _ in range(3):
            self._get_related_company_response(
                requests_mock,
                tree_members,
                target_company_dh,
                query_param,
            )

        assert validate_company_id_mock.call_count <= 1


class TestRelatedCompaniesCountView(APITestMixin, TestHierarchyAPITestMixin):
    """DNB Company Hierarchy Search view test case."""

    def test_company_id_is_valid(self):
        assert (
            self.api_client.get(
                reverse(
                    'api-v4:dnb-api:related-companies-count',
                    kwargs={'company_id': '11223344'},
                ),
            ).status_code
            == 400
        )

    def test_company_has_no_company_id(self):
        assert (
            self.api_client.get(
                reverse('api-v4:dnb-api:related-companies-count', kwargs={'company_id': uuid4()}),
            ).status_code
            == 404
        )

    def test_company_has_no_duns_number(self):
        company = CompanyFactory(duns_number=None)
        assert (
            self.api_client.get(
                reverse(
                    'api-v4:dnb-api:related-companies-count',
                    kwargs={'company_id': company.id},
                ),
            ).status_code
            == 400
        )

    def test_dnb_company_count_of_0_returns_0(self, requests_mock):
        ultimate_company_dh = CompanyFactory(
            duns_number='123456789',
        )

        url = reverse(
            'api-v4:dnb-api:related-companies-count',
            kwargs={'company_id': ultimate_company_dh.id},
        )

        self.set_dnb_hierarchy_count_mock_response(requests_mock, 0)

        response = self.api_client.get(
            f'{url}?include_manually_linked_companies=false',
        ).json()

        assert response['related_companies_count'] == 0
        assert response['manually_linked_subsidiaries_count'] == 0
        assert response['total'] == 0

    def test_dnb_company_count_of_0_and_subsidiary_count_of_0_returns_0(self, requests_mock):
        ultimate_company_dh = CompanyFactory(
            duns_number='123456789',
        )

        url = reverse(
            'api-v4:dnb-api:related-companies-count',
            kwargs={'company_id': ultimate_company_dh.id},
        )
        self.set_dnb_hierarchy_count_mock_response(requests_mock, 0)

        response = self.api_client.get(
            f'{url}?include_manually_linked_companies=true',
        ).json()

        assert response['related_companies_count'] == 0
        assert response['manually_linked_subsidiaries_count'] == 0
        assert response['total'] == 0

    def test_dnb_company_count_of_1_returns_0(self, requests_mock):
        ultimate_company_dh = CompanyFactory(
            duns_number='123456789',
        )

        url = reverse(
            'api-v4:dnb-api:related-companies-count',
            kwargs={'company_id': ultimate_company_dh.id},
        )

        self.set_dnb_hierarchy_count_mock_response(requests_mock, 0)

        response = self.api_client.get(
            f'{url}?include_manually_linked_companies=false',
        ).json()

        assert response['related_companies_count'] == 0
        assert response['manually_linked_subsidiaries_count'] == 0
        assert response['total'] == 0

    def test_dnb_company_count_of_0_and_subsidiary_count_of_1_returns_1(self, requests_mock):
        ultimate_company_dh = CompanyFactory(
            duns_number='123456789',
        )

        CompanyFactory(global_headquarters_id=ultimate_company_dh.id)

        url = reverse(
            'api-v4:dnb-api:related-companies-count',
            kwargs={'company_id': ultimate_company_dh.id},
        )
        self.set_dnb_hierarchy_count_mock_response(requests_mock, 0)

        response = self.api_client.get(
            f'{url}?include_manually_linked_companies=true',
        ).json()

        assert response['related_companies_count'] == 0
        assert response['manually_linked_subsidiaries_count'] == 1
        assert response['total'] == 1

    def test_dnb_company_count_of_1_and_subsidiary_count_of_1_returns_1(self, requests_mock):
        ultimate_company_dh = CompanyFactory(
            duns_number='123456789',
        )

        CompanyFactory(global_headquarters_id=ultimate_company_dh.id)

        url = reverse(
            'api-v4:dnb-api:related-companies-count',
            kwargs={'company_id': ultimate_company_dh.id},
        )
        self.set_dnb_hierarchy_count_mock_response(requests_mock, 1)

        response = self.api_client.get(
            f'{url}?include_manually_linked_companies=true',
        ).json()

        assert response['related_companies_count'] == 0
        assert response['manually_linked_subsidiaries_count'] == 1
        assert response['total'] == 1

    def test_dnb_company_count_of_1_and_subsidiary_count_of_1_excluding_subsidiaries_returns_0(
        self,
        requests_mock,
    ):
        ultimate_company_dh = CompanyFactory(
            duns_number='123456789',
        )

        CompanyFactory(global_headquarters_id=ultimate_company_dh.id)

        url = reverse(
            'api-v4:dnb-api:related-companies-count',
            kwargs={'company_id': ultimate_company_dh.id},
        )
        self.set_dnb_hierarchy_count_mock_response(requests_mock, 1)

        response = self.api_client.get(
            f'{url}?include_manually_linked_companies=false',
        ).json()

        assert response['related_companies_count'] == 0
        assert response['manually_linked_subsidiaries_count'] == 0
        assert response['total'] == 0

    def test_dnb_company_count_of_10_and_subsidiary_count_of_3_returns_12(self, requests_mock):
        ultimate_company_dh = CompanyFactory(
            duns_number='123456789',
        )

        CompanyFactory.create_batch(3, global_headquarters_id=ultimate_company_dh.id)

        url = reverse(
            'api-v4:dnb-api:related-companies-count',
            kwargs={'company_id': ultimate_company_dh.id},
        )
        self.set_dnb_hierarchy_count_mock_response(requests_mock, 10)
        response = self.api_client.get(
            f'{url}?include_manually_linked_companies=true',
        ).json()

        assert response['related_companies_count'] == 9
        assert response['manually_linked_subsidiaries_count'] == 3
        assert response['total'] == 12
        assert response['reduced_tree'] is not True

    def test_dnb_company_count_of_10000_and_subsidiary_count_of_3_returns_10002_and_reduced_tree(
        self,
        requests_mock,
    ):
        ultimate_company_dh = CompanyFactory(
            duns_number='123456789',
        )

        CompanyFactory.create_batch(3, global_headquarters_id=ultimate_company_dh.id)

        url = reverse(
            'api-v4:dnb-api:related-companies-count',
            kwargs={'company_id': ultimate_company_dh.id},
        )
        self.set_dnb_hierarchy_count_mock_response(requests_mock, 10000)
        response = self.api_client.get(
            f'{url}?include_manually_linked_companies=true',
        ).json()

        assert response['related_companies_count'] == 9999
        assert response['manually_linked_subsidiaries_count'] == 3
        assert response['total'] == 10002
        assert response['reduced_tree'] is True


class TestCompanyHierarchyReducedView(APITestMixin, TestHierarchyAPITestMixin):
    """DNB Company Hierarchy Reduced view test case."""

    def test_company_id_is_valid(self):
        assert (
            self.api_client.get(
                reverse('api-v4:dnb-api:reduced-family-tree', kwargs={'company_id': '11223344'}),
            ).status_code
            == 400
        )

    def test_company_has_no_company_id(self):
        assert (
            self.api_client.get(
                reverse('api-v4:dnb-api:reduced-family-tree', kwargs={'company_id': uuid4()}),
            ).status_code
            == 404
        )

    def test_company_has_no_duns_number(self):
        company = CompanyFactory(duns_number=None)
        assert (
            self.api_client.get(
                reverse('api-v4:dnb-api:reduced-family-tree', kwargs={'company_id': company.id}),
            ).status_code
            == 400
        )

    def test_empty_results_returned_from_dnb_service(
        self,
        requests_mock,
    ):
        """Test empty results from dnb proxy returns error."""
        company = CompanyFactory(duns_number='123456789')

        requests_mock.post(
            DNB_V2_SEARCH_URL,
            json={'results': []},
        )
        self.set_dnb_hierarchy_count_mock_response(requests_mock, 2)

        assert (
            self.api_client.get(
                reverse('api-v4:dnb-api:reduced-family-tree', kwargs={'company_id': company.id}),
            ).status_code
            == 502
        )

    def test_more_than_single_result_returned_from_dnb_service(
        self,
        requests_mock,
    ):
        """Test more than 1 result from dnb proxy returns error."""
        company = CompanyFactory(duns_number='123456789')

        requests_mock.post(
            DNB_V2_SEARCH_URL,
            json={'results': [{}, {}]},
        )
        self.set_dnb_hierarchy_count_mock_response(requests_mock, 2)

        assert (
            self.api_client.get(
                reverse('api-v4:dnb-api:reduced-family-tree', kwargs={'company_id': company.id}),
            ).status_code
            == 502
        )

    def test_single_result_returned_from_dnb_service_does_not_match_request(
        self,
        requests_mock,
    ):
        """Test when the result from dnb proxy does not match requested duns number."""
        company = CompanyFactory(duns_number='123456789')

        requests_mock.post(DNB_V2_SEARCH_URL, json={'results': [{'duns_number': '000000000'}]})
        self.set_dnb_hierarchy_count_mock_response(requests_mock, 2)

        assert (
            self.api_client.get(
                reverse('api-v4:dnb-api:reduced-family-tree', kwargs={'company_id': company.id}),
            ).status_code
            == 502
        )

    def test_reduced_family_tree_success(
        self,
        opensearch_with_signals,
    ):
        """Test when the result from dnb proxy is ok a valid tree is generated."""
        global_company = CompanyFactory(duns_number='111111111')
        company = CompanyFactory(duns_number='222222222', global_ultimate_duns_number='111111111')

        opensearch_with_signals.indices.refresh()
        with requests_mock.Mocker() as m:
            m.post(
                DNB_V2_SEARCH_URL,
                [
                    {
                        'json': {
                            'results': [
                                {'duns_number': '222222222', 'parent_duns_number': '111111111'},
                            ],
                        },
                    },
                    {
                        'json': {
                            'results': [{'duns_number': '111111111'}],
                        },
                    },
                ],
            )

            self.set_dnb_hierarchy_count_mock_response(m, 2)

            response = self.api_client.get(
                reverse('api-v4:dnb-api:reduced-family-tree', kwargs={'company_id': company.id}),
            )

            assert response.status_code == 200
            assert response.json() == {
                'ultimate_global_company': {
                    'duns_number': global_company.duns_number,
                    'name': global_company.name,
                    'number_of_employees': global_company.number_of_employees,
                    'id': str(global_company.id),
                    'address': {
                        'country': {
                            'id': str(global_company.address_country.id),
                            'name': global_company.address_country.name,
                        },
                        'county': '',
                        'line_1': global_company.address_1,
                        'line_2': '',
                        'postcode': global_company.address_postcode,
                        'town': global_company.address_town,
                    },
                    'registered_address': {
                        'country': {
                            'id': str(global_company.registered_address_country.id),
                            'name': global_company.registered_address_country.name,
                        },
                        'county': '',
                        'line_1': global_company.registered_address_1,
                        'line_2': '',
                        'postcode': global_company.registered_address_postcode,
                        'town': global_company.registered_address_town,
                    },
                    'sector': {
                        'id': str(global_company.sector.id),
                        'name': global_company.sector.name,
                    },
                    'trading_names': [],
                    'headquarter_type': global_company.headquarter_type,
                    'uk_region': {
                        'id': str(global_company.uk_region.id),
                        'name': global_company.uk_region.name,
                    },
                    'one_list_tier': None,
                    'archived': global_company.archived,
                    'latest_interaction_date': None,
                    'hierarchy': 1,
                    'is_out_of_business': None,
                    'subsidiaries': [
                        {
                            'duns_number': company.duns_number,
                            'id': str(company.id),
                            'name': company.name,
                            'number_of_employees': company.number_of_employees,
                            'address': {
                                'country': {
                                    'id': str(company.address_country.id),
                                    'name': company.address_country.name,
                                },
                                'county': '',
                                'line_1': company.address_1,
                                'line_2': '',
                                'postcode': company.address_postcode,
                                'town': company.address_town,
                            },
                            'registered_address': {
                                'country': {
                                    'id': str(company.registered_address_country.id),
                                    'name': company.registered_address_country.name,
                                },
                                'county': '',
                                'line_1': company.registered_address_1,
                                'line_2': '',
                                'postcode': company.registered_address_postcode,
                                'town': company.registered_address_town,
                            },
                            'sector': {
                                'id': str(company.sector.id),
                                'name': company.sector.name,
                            },
                            'trading_names': [],
                            'headquarter_type': company.headquarter_type,
                            'uk_region': {
                                'id': str(company.uk_region.id),
                                'name': company.uk_region.name,
                            },
                            'one_list_tier': None,
                            'archived': False,
                            'latest_interaction_date': None,
                            'hierarchy': 2,
                            'is_out_of_business': None,
                        },
                    ],
                },
                'ultimate_global_companies_count': 2,
                'manually_verified_subsidiaries': [],
                'reduced_tree': True,
                'family_tree_companies_count': 2,
            }
