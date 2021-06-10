import json
from unittest.mock import Mock
from urllib.parse import urljoin
from uuid import UUID

import pytest
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test.utils import override_settings
from freezegun import freeze_time
from requests.exceptions import (
    ConnectionError,
    Timeout,
)
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.models import Company, CompanyPermission
from datahub.company.test.factories import CompanyFactory
from datahub.core import constants
from datahub.core.serializers import AddressSerializer
from datahub.core.test_utils import APITestMixin, create_test_user
from datahub.dnb_api.constants import ALL_DNB_UPDATED_SERIALIZER_FIELDS
from datahub.dnb_api.utils import (
    DNBServiceConnectionError,
    DNBServiceTimeoutError,
    format_dnb_company,
)
from datahub.interaction.models import InteractionPermission
from datahub.metadata.models import Country

DNB_SEARCH_URL = urljoin(f'{settings.DNB_SERVICE_BASE_URL}/', 'companies/search/')
DNB_CHANGE_REQUEST_URL = urljoin(f'{settings.DNB_SERVICE_BASE_URL}/', 'change-request/')
DNB_INVESTIGATION_URL = urljoin(f'{settings.DNB_SERVICE_BASE_URL}/', 'investigation/')

REQUIRED_REGISTERED_ADDRESS_FIELDS = [
    f'registered_address_{field}' for field in AddressSerializer.REQUIRED_FIELDS
]


@pytest.mark.parametrize(
    'url',
    (
        reverse('api-v4:dnb-api:company-search'),
        reverse('api-v4:dnb-api:company-create'),
        reverse('api-v4:dnb-api:company-link'),
        reverse('api-v4:dnb-api:company-change-request'),
    ),
)
class TestDNBAPICommon(APITestMixin):
    """
    Test common functionality in company-search as well
    as company-create endpoints.
    """

    def test_unauthenticated_not_authorised(
        self,
        requests_mock,
        url,
    ):
        """
        Ensure that a non-authenticated request gets a 401.
        """
        requests_mock.post(DNB_SEARCH_URL)

        unauthorised_api_client = self.create_api_client()
        unauthorised_api_client.credentials(HTTP_AUTHORIZATION='foo')

        response = unauthorised_api_client.post(
            url,
            data={'foo': 'bar'},
        )

        assert response.status_code == 401
        assert requests_mock.called is False


class TestDNBCompanySearchAPI(APITestMixin):
    """
    DNB Company Search view test case.
    """

    @override_settings(DNB_SERVICE_BASE_URL=None)
    def test_post_no_dnb_setting(self):
        """
        Test that we get an ImproperlyConfigured exception when the DNB_SERVICE_BASE_URL setting
        is not set.
        """
        with pytest.raises(ImproperlyConfigured):
            self.api_client.post(
                reverse('api-v4:dnb-api:company-search'),
                data={},
            )

    @pytest.mark.parametrize(
        'content_type,expected_status_code',
        (
            (None, status.HTTP_406_NOT_ACCEPTABLE),
            ('text/html', status.HTTP_406_NOT_ACCEPTABLE),
        ),
    )
    def test_content_type(
        self,
        requests_mock,
        dnb_response_non_uk,
        content_type,
        expected_status_code,
    ):
        """
        Test that 406 is returned if Content Type is not application/json.
        """
        requests_mock.post(
            DNB_SEARCH_URL,
            status_code=status.HTTP_200_OK,
            json=dnb_response_non_uk,
        )

        response = self.api_client.post(
            reverse('api-v4:dnb-api:company-search'),
            content_type=content_type,
        )

        assert response.status_code == expected_status_code

    @pytest.mark.parametrize(
        'request_data,response_status_code,upstream_response_content,response_data',
        (
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
            pytest.param(
                b'{"arg": "value"}',
                400,
                b'{"error":"msg"}',
                {'error': 'msg'},
                id='proxied API returns a bad request',
            ),
            pytest.param(
                b'{"arg": "value"}',
                500,
                b'{"error":"msg"}',
                {'error': 'msg'},
                id='proxied API returns a server error',
            ),
        ),
    )
    def test_post(
        self,
        dnb_company_search_datahub_companies,
        requests_mock,
        request_data,
        response_status_code,
        upstream_response_content,
        response_data,
    ):
        """
        Test for POST proxy.
        """
        requests_mock.post(
            DNB_SEARCH_URL,
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
        'response_status_code,upstream_response_content,response_data,permission_codenames',
        (
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
        ),
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
        """
        Test for POST proxy permissions.
        """
        requests_mock.post(
            DNB_SEARCH_URL,
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

    @pytest.mark.parametrize(
        'response_status_code',
        (
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ),
    )
    def test_monitoring(
        self,
        monkeypatch,
        requests_mock,
        response_status_code,
    ):
        """
        Test that the right counter is incremented for the given status code
        returned by the dnb-service.
        """
        statsd_mock = Mock()
        monkeypatch.setattr('datahub.dnb_api.utils.statsd', statsd_mock)
        requests_mock.post(
            DNB_SEARCH_URL,
            status_code=response_status_code,
            json={},
        )
        self.api_client.post(
            reverse('api-v4:dnb-api:company-search'),
            content_type='application/json',
        )
        statsd_mock.incr.assert_called_once_with(
            f'dnb.search.{response_status_code}',
        )


class TestDNBCompanyCreateAPI(APITestMixin):
    """
    DNB Company Create view test case.
    """

    def _assert_companies_same(self, company, dnb_company):
        """
        Check whether the given DataHub company is the same as the given DNB company.
        """
        country = Country.objects.filter(
            iso_alpha2_code=dnb_company['address_country'],
        ).first()
        registered_country = Country.objects.filter(
            iso_alpha2_code=dnb_company['registered_address_country'],
        ).first() if dnb_company.get('registered_address_country') else None

        company_number = (
            dnb_company['registration_numbers'][0].get('registration_number')
            if country.iso_alpha2_code == 'GB' else None
        )

        [company.pop(k) for k in ('id', 'created_on', 'modified_on')]

        required_registered_address_fields_present = all(
            field in dnb_company for field in REQUIRED_REGISTERED_ADDRESS_FIELDS
        )
        registered_address = {
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
        } if required_registered_address_fields_present else None

        assert company == {
            'name': dnb_company['primary_name'],
            'trading_names': dnb_company['trading_names'],
            'address': {
                'area': None,
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
        }

    @override_settings(DNB_SERVICE_BASE_URL=None)
    def test_post_no_dnb_setting(self):
        """
        Test that we get an ImproperlyConfigured exception when the DNB_SERVICE_BASE_URL setting
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
        """
        Test create-company endpoint for a non-uk company.
        """
        requests_mock.post(
            DNB_SEARCH_URL,
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
        """
        Test create-company endpoint for a UK company.
        """
        requests_mock.post(
            DNB_SEARCH_URL,
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
        (
            {'duns_number': None},
            {'duns_number': 'foobarbaz'},
            {'duns_number': '12345678'},
            {'duns_number': '1234567890'},
            {'not_duns_number': '123456789'},
        ),
    )
    def test_post_invalid(
        self,
        data,
    ):
        """
        Test that a query without `duns_number` returns 400.
        """
        response = self.api_client.post(
            reverse('api-v4:dnb-api:company-create'),
            data=data,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.parametrize(
        'results, expected_status_code, expected_message',
        (
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
        ),
    )
    def test_post_none_or_multiple_companies_found(
        self,
        requests_mock,
        results,
        expected_status_code,
        expected_message,
    ):
        """
        Test if a given `duns_number` gets anything other than a single company
        from dnb-service, the create-company endpoint returns a 400.

        """
        requests_mock.post(
            DNB_SEARCH_URL,
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
        'missing_required_field, expected_error',
        (
            ('primary_name', {'name': ['This field may not be null.']}),
            ('trading_names', {'trading_names': ['This field may not be null.']}),
            ('address_line_1', {'address': {'line_1': ['This field is required.']}}),
            ('address_town', {'address': {'town': ['This field is required.']}}),
            ('address_country', {'address': {'country': ['This field is required.']}}),
        ),
    )
    def test_post_missing_required_fields(
        self,
        requests_mock,
        dnb_response_uk,
        missing_required_field,
        expected_error,
    ):
        """
        Test if dnb-service returns a company with missing required fields,
        the create-company endpoint returns 400.
        """
        dnb_response_uk['results'][0].pop(missing_required_field)
        requests_mock.post(
            DNB_SEARCH_URL,
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
        (
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
        ),
    )
    def test_post_missing_optional_fields(
        self,
        requests_mock,
        dnb_response_uk,
        field_overrides,
    ):
        """
        Test if dnb-service returns a company with missing optional fields,
        the create-company endpoint still returns 200 and the company is saved
        successfully.
        """
        dnb_response_uk['results'][0].update(field_overrides)
        requests_mock.post(
            DNB_SEARCH_URL,
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
        """
        Test if create-company endpoint returns 400 if the company with the given
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
            'duns_number': [
                f'Company with duns_number: {duns_number} already exists in DataHub.'],
        }

    def test_post_invalid_country(
        self,
        requests_mock,
        dnb_response_uk,
    ):
        """
        Test if create-company endpoint returns 400 if the company is based in a country
        that does not exist in DataHub.
        """
        dnb_response_uk['results'][0]['address_country'] = 'FOO'
        requests_mock.post(
            DNB_SEARCH_URL,
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
        (
            {'global_ultimate_duns_number': 'foobarbaz'},
            {'global_ultimate_duns_number': '12345678'},
            {'global_ultimate_duns_number': '1234567890'},
        ),
    )
    def test_post_invalid_global_ultimate(
        self,
        requests_mock,
        dnb_response_uk,
        global_ultimate_override,
    ):
        """
        Test if create-company endpoint returns 400 if the global_ultimate_duns_number
        returned from D&B is invalid.
        """
        dnb_response_uk['results'][0]['global_ultimate_duns_number'] = global_ultimate_override
        requests_mock.post(
            DNB_SEARCH_URL,
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
        (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_405_METHOD_NOT_ALLOWED,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            status.HTTP_502_BAD_GATEWAY,
        ),
    )
    def test_post_dnb_service_error(
        self,
        requests_mock,
        status_code,
    ):
        """
        Test if create-company endpoint returns 400 if the company is based in a country
        that does not exist in DataHub.
        """
        requests_mock.post(
            DNB_SEARCH_URL,
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
        """
        Test if create-company endpoint returns 400 if the company is based in a country
        that does not exist in DataHub.
        """
        requests_mock.post(
            DNB_SEARCH_URL,
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
        (
            [],
            [CompanyPermission.add_company],
            [CompanyPermission.view_company],
        ),
    )
    def test_post_no_permission(
        self,
        requests_mock,
        dnb_response_uk,
        permissions,
    ):
        """
        Create-company endpoint should return 403 if the user does not
        have the necessary permissions.
        """
        requests_mock.post(
            DNB_SEARCH_URL,
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

    @pytest.mark.parametrize(
        'response_status_code',
        (
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ),
    )
    def test_monitoring_search(
        self,
        monkeypatch,
        requests_mock,
        response_status_code,
    ):
        """
        Test that the right counter is incremented for the given status code
        returned by the dnb-service.
        """
        statsd_mock = Mock()
        monkeypatch.setattr('datahub.dnb_api.utils.statsd', statsd_mock)
        requests_mock.post(
            DNB_SEARCH_URL,
            status_code=response_status_code,
            json={},
        )
        self.api_client.post(
            reverse('api-v4:dnb-api:company-create'),
            data={
                'duns_number': 123456789,
            },
        )
        statsd_mock.incr.assert_called_once_with(
            f'dnb.search.{response_status_code}',
        )

    def test_monitoring_create(
        self,
        monkeypatch,
        dnb_response_uk,
        requests_mock,
    ):
        """
        Test that the right counter is incremented when a company gets
        created using dnb-service.
        """
        statsd_mock = Mock()
        monkeypatch.setattr('datahub.dnb_api.views.statsd', statsd_mock)
        requests_mock.post(
            DNB_SEARCH_URL,
            status_code=status.HTTP_200_OK,
            json=dnb_response_uk,
        )
        self.api_client.post(
            reverse('api-v4:dnb-api:company-create'),
            data={
                'duns_number': 123456789,
            },
        )
        statsd_mock.incr.assert_called_with(
            'dnb.create.company',
        )


class TestCompanyLinkView(APITestMixin):
    """
    Test POST `/dnb/company-link` endpoint.
    """

    @pytest.mark.parametrize(
        'content_type,expected_status_code',
        (
            (None, status.HTTP_406_NOT_ACCEPTABLE),
            ('text/html', status.HTTP_406_NOT_ACCEPTABLE),
        ),
    )
    def test_content_type(
        self,
        content_type,
        expected_status_code,
    ):
        """
        Test that 406 is returned if Content Type is not application/json.
        """
        response = self.api_client.post(
            reverse('api-v4:dnb-api:company-link'),
            content_type=content_type,
        )

        assert response.status_code == expected_status_code

    @pytest.mark.parametrize(
        'permissions',
        (
            [],
            [CompanyPermission.change_company],
            [CompanyPermission.view_company],
        ),
    )
    def test_no_permission(
        self,
        permissions,
    ):
        """
        The endpoint should return 403 if the user does not have the necessary permissions.
        """
        user = create_test_user(permission_codenames=permissions)
        api_client = self.create_api_client(user=user)
        response = api_client.post(
            reverse('api-v4:dnb-api:company-link'),
            data={},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize(
        'override',
        (
            {'duns_number': None},
            {'duns_number': 'foobarbaz'},
            {'duns_number': '12345678'},
            {'duns_number': '1234567890'},
            {'company_id': None},
            {'company_id': 'does-not-exist'},
            {'company_id': '11111111-2222-3333-4444-555555555555'},
        ),
    )
    def test_invalid(
        self,
        override,
    ):
        """
        Test that a query without a valid `duns_number` returns 400.
        """
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
        (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_405_METHOD_NOT_ALLOWED,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            status.HTTP_502_BAD_GATEWAY,
        ),
    )
    def test_dnb_service_error(
        self,
        requests_mock,
        status_code,
    ):
        """
        Test if company-link endpoint returns 502 if the upstream
        `dnb-service` returns an error.
        """
        company = CompanyFactory()
        requests_mock.post(
            DNB_SEARCH_URL,
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
        """
        Test that the endpoint returns 400 for a company that is already linked.
        """
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
            'detail': f'Company {str(company.id)} is already linked '
                      'with duns number 123456789',
        }

    def test_duplicate_duns_number(self):
        """
        Test that the endpoint returns 400 if we try to link a company to a D&B record
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
        """
        Test that when a duns_number does not return any company from
        dnb-service, the endpoint returns 400 status.
        """
        company = CompanyFactory()
        requests_mock.post(
            DNB_SEARCH_URL,
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
        """
        Test that valid request to company-link endpoint returns 200.
        """
        company = CompanyFactory()
        requests_mock.post(
            DNB_SEARCH_URL,
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
    """
    Test POST `/dnb/company-change-request` endpoint.
    """

    @pytest.mark.parametrize(
        'content_type,expected_status_code',
        (
            (None, status.HTTP_406_NOT_ACCEPTABLE),
            ('text/html', status.HTTP_406_NOT_ACCEPTABLE),
        ),
    )
    def test_content_type(
        self,
        content_type,
        expected_status_code,
    ):
        """
        Test that 406 is returned if Content Type is not application/json.
        """
        response = self.api_client.post(
            reverse('api-v4:dnb-api:company-change-request'),
            content_type=content_type,
        )

        assert response.status_code == expected_status_code

    @pytest.mark.parametrize(
        'permissions',
        (
            [],
            [CompanyPermission.change_company],
            [CompanyPermission.view_company],
        ),
    )
    def test_no_permission(
        self,
        permissions,
    ):
        """
        The endpoint should return 403 if the user does not have the necessary permissions.
        """
        user = create_test_user(permission_codenames=permissions)
        api_client = self.create_api_client(user=user)
        response = api_client.post(
            reverse('api-v4:dnb-api:company-change-request'),
            data={},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_company_does_not_exist(self):
        """
        The endpoint should return 400 if the company with the given
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
        'change_request,expected_response',
        (
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
        ),
    )
    def test_invalid_fields(
        self,
        change_request,
        expected_response,
    ):
        """
        Test that invalid payload results in 400 and an appropriate
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
        'change_request,dnb_request,dnb_response,datahub_response',
        (

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
                            'area_name': 'California',
                            'area_abbrev_name': 'CA',
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
                        'address_area_name': 'California',
                        'address_area_abbrev_name': 'CA',
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
                        'address_area_name': 'California',
                        'address_area_abbrev_name': 'CA',
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
                        'address_area_name': 'California',
                        'address_area_abbrev_name': 'CA',
                        'address_country': 'US',
                        'address_postcode': '91012',
                        'employee_number': 100,
                        'annual_sales': 1000,
                    },
                },
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
            ),

            # Address area is not selected
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
                        'address_area_name': '',
                        'address_area_abbrev_name': '',
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
                        'address_area_name': '',
                        'address_area_abbrev_name': '',
                        'address_country': 'GB',
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
                        'address_area_name': '',
                        'address_area_abbrev_name': '',
                        'address_country': 'GB',
                        'address_postcode': 'W1 0TN',
                        'employee_number': 100,
                        'annual_sales': 1000,
                    },
                },
            ),
        ),
    )
    def test_valid(
        self,
        requests_mock,
        change_request,
        dnb_request,
        dnb_response,
        datahub_response,
    ):
        """
        The endpoint should return 200 as well as a valid response
        when it is hit with a valid payload.
        """
        CompanyFactory(duns_number='123456789')

        requests_mock.post(
            DNB_CHANGE_REQUEST_URL,
            status_code=status.HTTP_201_CREATED,
            json=dnb_response,
        )

        response = self.api_client.post(
            reverse('api-v4:dnb-api:company-change-request'),
            data=change_request,
        )

        assert requests_mock.last_request.json() == dnb_request
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == datahub_response

    @pytest.mark.parametrize(
        'status_code',
        (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_405_METHOD_NOT_ALLOWED,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            status.HTTP_502_BAD_GATEWAY,
        ),
    )
    def test_dnb_service_error(
        self,
        requests_mock,
        status_code,
    ):
        """
        The  endpoint should return 502 if the upstream
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
        """
        Test that we get an ImproperlyConfigured exception when the DNB_SERVICE_BASE_URL setting
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
        'request_exception, expected_exception, expected_message',
        (
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
        ),
    )
    def test_request_error(
        self,
        requests_mock,
        request_exception,
        expected_exception,
        expected_message,
    ):
        """
        Test if there is an error connecting to dnb-service, we raise the
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
        """
        Test that a partial change-request to address sends
        all address fields to dnb-service.
        """
        company = CompanyFactory(duns_number='123456789')
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
            },
        }

    """
    Test GET `/dnb/company-change-request` endpoint.
    """

    @pytest.mark.parametrize(
        'request_exception, expected_exception, expected_message',
        (
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
        ),
    )
    def test_get_request_error(
        self,
        requests_mock,
        request_exception,
        expected_exception,
        expected_message,
    ):
        """
        Test if there is an error connecting to dnb-service, we raise the
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
        'dnb_request,dnb_response',
        (
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
        ),
    )
    def test_that_pending_request_returns_correctly(
        self,
        requests_mock,
        dnb_request,
        dnb_response,
    ):
        """
        Test that pending change requests stored in the dnb-service can be
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
        'change_request,expected_response',
        (
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
        ),
    )
    def test_invalid_fields_for_get(
        self,
        change_request,
        expected_response,
    ):
        """
        Test that invalid payload results in 400 and an appropriate
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
    """
    Test POST `/dnb/company-investigation` endpoint.
    """

    @pytest.mark.parametrize(
        'content_type,expected_status_code',
        (
            (None, status.HTTP_406_NOT_ACCEPTABLE),
            ('text/html', status.HTTP_406_NOT_ACCEPTABLE),
        ),
    )
    def test_content_type(
        self,
        content_type,
        expected_status_code,
    ):
        """
        Test that 406 is returned if Content Type is not application/json.
        """
        response = self.api_client.post(
            reverse('api-v4:dnb-api:company-investigation'),
            content_type=content_type,
        )

        assert response.status_code == expected_status_code

    def test_unauthenticated_not_authorised(self):
        """
        Ensure that a non-authenticated request gets a 401.
        """
        unauthorised_api_client = self.create_api_client()
        unauthorised_api_client.credentials(HTTP_AUTHORIZATION='foo')

        response = unauthorised_api_client.post(
            reverse('api-v4:dnb-api:company-investigation'),
            data={},
        )

        assert response.status_code == 401

    @pytest.mark.parametrize(
        'permissions',
        (
            [],
            [CompanyPermission.change_company],
            [CompanyPermission.view_company],
        ),
    )
    def test_no_permission(
        self,
        permissions,
    ):
        """
        The endpoint should return 403 if the user does not have the necessary permissions.
        """
        user = create_test_user(permission_codenames=permissions)
        api_client = self.create_api_client(user=user)
        response = api_client.post(
            reverse('api-v4:dnb-api:company-investigation'),
            data={},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_company_does_not_exist(self):
        """
        The endpoint should return 400 if the company when the given company ID does not exist.
        """
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
        'investigation_request_overrides,expected_response',
        (
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
        ),
    )
    def test_invalid_fields(
        self,
        investigation_request_overrides,
        expected_response,
    ):
        """
        Test that invalid payload results in 400 and an appropriate error message.
        """
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
        """
        The endpoint should return 200 as well as a valid response when it is hit with a valid
        payload of full investigation details.
        """
        company = CompanyFactory()
        dnb_formatted_company_details = {
            'company_details': {
                'primary_name': 'Joe Bloggs LTD',
                'domain': 'www.example.com',
                'telephone_number': '123456789',
                'address_line_1': '23 Code Street',
                'address_line_2': 'Someplace',
                'address_town': 'Beverly Hills',
                'address_county': 'Los Angeles',
                'address_area_name': 'California',
                'address_area_abbrev_name': 'CA',
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
                    'area_name': 'California',
                    'area_abbrev_name': 'CA',
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
        'missing_field_data_hub, missing_field_dnb_service',
        (
            ('website', 'domain'),
            ('telephone_number', 'telephone_number'),
        ),
    )
    def test_valid_minimum_data(
        self,
        requests_mock,
        missing_field_data_hub,
        missing_field_dnb_service,
    ):
        """
        The endpoint should return 200 as well as a valid response when it is hit with a valid
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
        (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_405_METHOD_NOT_ALLOWED,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            status.HTTP_502_BAD_GATEWAY,
        ),
    )
    def test_dnb_service_error(
        self,
        requests_mock,
        status_code,
    ):
        """
        The  endpoint should return 502 if the upstream `dnb-service` returns an error.
        """
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
        """
        Test that we get an ImproperlyConfigured exception when the DNB_SERVICE_BASE_URL setting
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
        'request_exception, expected_exception, expected_message',
        (
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
        ),
    )
    def test_request_error(
        self,
        requests_mock,
        request_exception,
        expected_exception,
        expected_message,
    ):
        """
        Test if there is an error connecting to dnb-service, we raise the
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
