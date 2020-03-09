from urllib.parse import urljoin
from uuid import UUID

import pytest
import reversion
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test.utils import override_settings
from django.utils.timezone import now
from freezegun import freeze_time
from requests.exceptions import (
    ConnectionError,
    ConnectTimeout,
    ReadTimeout,
    Timeout,
)
from rest_framework import serializers, status
from reversion.models import Version

from datahub.company.models import Company
from datahub.company.test.factories import AdviserFactory, CompanyFactory
from datahub.dnb_api.constants import ALL_DNB_UPDATED_MODEL_FIELDS
from datahub.dnb_api.test.utils import model_to_dict_company
from datahub.dnb_api.utils import (
    DNBServiceConnectionError,
    DNBServiceError,
    DNBServiceInvalidRequest,
    DNBServiceInvalidResponse,
    DNBServiceTimeoutError,
    format_dnb_company,
    get_company,
    get_company_update_page,
    request_changes,
    RevisionNotFoundError,
    rollback_dnb_company_update,
    update_company_from_dnb,
)
from datahub.metadata.models import Country

pytestmark = pytest.mark.django_db


DNB_SEARCH_URL = urljoin(f'{settings.DNB_SERVICE_BASE_URL}/', 'companies/search/')
DNB_UPDATES_URL = urljoin(f'{settings.DNB_SERVICE_BASE_URL}/', 'companies/')
DNB_CHANGE_REQUEST_URL = urljoin(f'{settings.DNB_SERVICE_BASE_URL}/', 'change-request/')


@pytest.mark.parametrize(
    'dnb_response_status',
    (
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
        status.HTTP_405_METHOD_NOT_ALLOWED,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    ),
)
def test_get_company_dnb_service_error(
    caplog,
    requests_mock,
    dnb_response_status,
):
    """
    Test if the dnb-service returns a status code that is not
    200, we log it and raise the exception with an appropriate
    message.
    """
    requests_mock.post(
        DNB_SEARCH_URL,
        status_code=dnb_response_status,
    )

    with pytest.raises(DNBServiceError) as e:
        get_company('123456789')

    expected_message = f'DNB service returned an error status: {dnb_response_status}'

    assert e.value.args[0] == expected_message
    assert len(caplog.records) == 1
    assert caplog.records[0].getMessage() == expected_message


@pytest.mark.parametrize(
    'request_exception,expected_exception,expected_message',
    (
        (
            ConnectionError,
            DNBServiceConnectionError,
            'Encountered an error connecting to DNB service',
        ),
        (
            ConnectTimeout,
            DNBServiceConnectionError,
            'Encountered an error connecting to DNB service',
        ),
        (
            Timeout,
            DNBServiceTimeoutError,
            'Encountered a timeout interacting with DNB service',
        ),
        (
            ReadTimeout,
            DNBServiceTimeoutError,
            'Encountered a timeout interacting with DNB service',
        ),
    ),
)
def test_get_company_dnb_service_request_error(
    caplog,
    requests_mock,
    request_exception,
    expected_exception,
    expected_message,
):
    """
    Test if there is an error connecting to dnb-service, we log it and raise the exception with an
    appropriate message.
    """
    requests_mock.post(
        DNB_SEARCH_URL,
        exc=request_exception,
    )

    with pytest.raises(expected_exception) as e:
        get_company('123456789')

    assert e.value.args[0] == expected_message
    assert len(caplog.records) == 1
    assert caplog.records[0].getMessage() == expected_message


@pytest.mark.parametrize(
    'search_results, expected_exception, expected_message',
    (
        (
            [],
            DNBServiceInvalidRequest,
            'Cannot find a company with duns_number: 123456789',
        ),
        (
            ['foo', 'bar'],
            DNBServiceInvalidResponse,
            'Multiple companies found with duns_number: 123456789',
        ),
        (
            [{'duns_number': '012345678'}],
            DNBServiceInvalidResponse,
            'DUNS number of the company: 012345678 '
            'did not match searched DUNS number: 123456789',
        ),
    ),
)
def test_get_company_invalid_request_response(
    caplog,
    requests_mock,
    search_results,
    expected_exception,
    expected_message,
):
    """
    Test if a given `duns_number` gets anything other than a single company
    from dnb-service, the get_company function raises an exception.
    """
    requests_mock.post(
        DNB_SEARCH_URL,
        json={'results': search_results},
    )

    with pytest.raises(expected_exception) as e:
        get_company('123456789')

    assert e.value.args[0] == expected_message
    assert len(caplog.records) == 1
    assert caplog.records[0].getMessage() == expected_message


def test_get_company_valid(
    caplog,
    requests_mock,
    dnb_response_uk,
):
    """
    Test if dnb-service returns a valid response, get_company
    returns a formatted dict.
    """
    requests_mock.post(
        DNB_SEARCH_URL,
        json=dnb_response_uk,
    )

    dnb_company = get_company('123456789')

    assert dnb_company == {
        'company_number': '01261539',
        'name': 'FOO BICYCLE LIMITED',
        'duns_number': '123456789',
        'trading_names': [],
        'address': {
            'country': UUID('80756b9a-5d95-e211-a939-e4115bead28a'),
            'county': '',
            'line_1': 'Unit 10, Ockham Drive',
            'line_2': '',
            'postcode': 'UB6 0F2',
            'town': 'GREENFORD',
        },
        'registered_address': {
            'country': UUID('80756b9a-5d95-e211-a939-e4115bead28a'),
            'county': '',
            'line_1': 'C/O LONE VARY',
            'line_2': '',
            'postcode': 'UB6 0F2',
            'town': 'GREENFORD',
        },
        'number_of_employees': 260,
        'is_number_of_employees_estimated': True,
        'turnover': 50651895.0,
        'is_turnover_estimated': None,
        'uk_based': True,
        'website': 'http://foo.com',
        'global_ultimate_duns_number': '291332174',
    }


class TestUpdateCompanyFromDNB:
    """
    Test update_company_from_dnb utility function.
    """

    @pytest.mark.parametrize(
        'adviser_callable',
        (
            lambda: None,
            lambda: AdviserFactory(),
        ),
    )
    @pytest.mark.parametrize(
        'update_descriptor',
        (
            None,
            'automatic',
        ),
    )
    @freeze_time('2019-01-01 11:12:13')
    def test_update_company_from_dnb_all_fields(
        self,
        formatted_dnb_company,
        adviser_callable,
        update_descriptor,
    ):
        """
        Test that update_company_from_dnb will update all fields when the fields
        kwarg is not specified.
        """
        duns_number = '123456789'
        company = CompanyFactory(duns_number=duns_number, pending_dnb_investigation=True)
        original_company = Company.objects.get(id=company.id)
        adviser = adviser_callable()
        update_company_from_dnb(
            company,
            formatted_dnb_company,
            user=adviser,
            update_descriptor=update_descriptor,
        )
        company.refresh_from_db()
        uk_country = Country.objects.get(iso_alpha2_code='GB')
        assert model_to_dict_company(company) == {
            'address_1': 'Unit 10, Ockham Drive',
            'address_2': '',
            'address_country': uk_country.id,
            'address_county': '',
            'address_postcode': 'UB6 0F2',
            'address_town': 'GREENFORD',
            'archived': False,
            'archived_by': None,
            'archived_documents_url_path': original_company.archived_documents_url_path,
            'archived_on': None,
            'archived_reason': None,
            'business_type': original_company.business_type.id,
            'company_number': '01261539',
            'created_by': original_company.created_by.id,
            'description': None,
            'dnb_investigation_data': None,
            'duns_number': '123456789',
            'employee_range': original_company.employee_range.id,
            'export_experience_category': original_company.export_experience_category.id,
            'export_potential': None,
            'export_to_countries': [],
            'future_interest_countries': [],
            'global_headquarters': None,
            'global_ultimate_duns_number': '291332174',
            'great_profile_status': None,
            'headquarter_type': None,
            'id': original_company.id,
            'is_number_of_employees_estimated': True,
            'is_turnover_estimated': None,
            'modified_by': adviser.id if adviser else original_company.modified_by.id,
            'name': 'FOO BICYCLE LIMITED',
            'number_of_employees': 260,
            'one_list_account_owner': None,
            'one_list_tier': None,
            'pending_dnb_investigation': False,
            'reference_code': '',
            'sector': original_company.sector.id,
            'trading_names': [],
            'transfer_reason': '',
            'transferred_by': None,
            'transferred_on': None,
            'transferred_to': None,
            'turnover': 50651895,
            'turnover_range': original_company.turnover_range.id,
            'uk_region': original_company.uk_region.id,
            'vat_number': '',
            'dnb_modified_on': now(),
        }

        versions = list(Version.objects.get_for_object(company))
        assert len(versions) == 1
        version = versions[0]

        if update_descriptor:
            assert version.revision.comment == f'Updated from D&B [{update_descriptor}]'
        else:
            assert version.revision.comment == 'Updated from D&B'

        assert version.revision.user == adviser
        if not adviser:
            assert company.modified_on == original_company.modified_on

    @pytest.mark.parametrize(
        'adviser_callable',
        (
            lambda: None,
            lambda: AdviserFactory(),
        ),
    )
    def test_update_company_from_dnb_partial_fields_single(
        self,
        formatted_dnb_company,
        adviser_callable,
    ):
        """
        Test that update_company_from_dnb can update a subset of fields.
        """
        duns_number = '123456789'
        company = CompanyFactory(duns_number=duns_number)
        original_company = Company.objects.get(id=company.id)
        adviser = adviser_callable()

        update_company_from_dnb(
            company,
            formatted_dnb_company,
            adviser,
            fields_to_update=['global_ultimate_duns_number'],
        )
        company.refresh_from_db()
        dnb_ultimate_duns = formatted_dnb_company['global_ultimate_duns_number']

        assert company.global_ultimate_duns_number == dnb_ultimate_duns
        assert company.name == original_company.name
        assert company.number_of_employees == original_company.number_of_employees

    @pytest.mark.parametrize(
        'adviser_callable',
        (
            lambda: None,
            lambda: AdviserFactory(),
        ),
    )
    def test_update_company_from_dnb_partial_fields_multiple(
        self,
        formatted_dnb_company,
        adviser_callable,
    ):
        """
        Test that update_company_from_dnb can update a subset of fields.
        """
        duns_number = '123456789'
        company = CompanyFactory(duns_number=duns_number)
        original_company = Company.objects.get(id=company.id)
        adviser = adviser_callable()

        update_company_from_dnb(
            company,
            formatted_dnb_company,
            adviser,
            fields_to_update=['name', 'address'],
        )
        company.refresh_from_db()

        assert company.global_ultimate_duns_number == original_company.global_ultimate_duns_number
        assert company.number_of_employees == original_company.number_of_employees
        assert company.name == formatted_dnb_company['name']
        assert company.address_1 == formatted_dnb_company['address']['line_1']
        assert company.address_2 == formatted_dnb_company['address']['line_2']
        assert company.address_town == formatted_dnb_company['address']['town']
        assert company.address_county == formatted_dnb_company['address']['county']
        assert company.address_postcode == formatted_dnb_company['address']['postcode']

    def test_post_dnb_data_invalid(
        self,
        formatted_dnb_company,
    ):
        """
        Tests that ValidationError is raised when data returned by DNB is not valid for saving to a
        Data Hub Company.
        """
        company = CompanyFactory(duns_number='123456789')
        adviser = AdviserFactory()
        formatted_dnb_company['name'] = None
        with pytest.raises(serializers.ValidationError) as excinfo:
            update_company_from_dnb(company, formatted_dnb_company, adviser)
            assert str(excinfo) == 'Data from D&B did not pass the Data Hub validation checks.'


class TestGetCompanyUpdatePage:
    """
    Test for the `get_company_update_page` utility function.
    """

    @pytest.mark.parametrize(
        'last_updated_after', (
            '2019-11-11T12:00:00',
            '2019-11-11',
        ),
    )
    @pytest.mark.parametrize(
        'next_page', (
            None,
            'http://some.url/endpoint?cursor=some-cursor',
        ),
    )
    def test_valid(self, requests_mock, last_updated_after, next_page):
        """
        Test if `get_company_update_page` returns the right response
        on the happy-path.
        """
        expected_response = {
            'previous': None,
            'next': f'{DNB_UPDATES_URL}?cursor=next-cursor',
            'results': [
                {'key': 'value'},
            ],
        }
        mocker = requests_mock.get(
            next_page if next_page else DNB_UPDATES_URL,
            status_code=status.HTTP_200_OK,
            json=expected_response,
        )
        response = get_company_update_page(last_updated_after, next_page)

        if next_page:
            assert mocker.last_request.url == next_page
        else:
            assert mocker.last_request.qs.get('last_updated_after') == [last_updated_after]

        assert response == expected_response

    @pytest.mark.parametrize(
        'dnb_response_status',
        (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_405_METHOD_NOT_ALLOWED,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ),
    )
    def test_dnb_service_error(
        self,
        caplog,
        requests_mock,
        dnb_response_status,
    ):
        """
        Test if the dnb-service returns a status code that is not
        200, we log it and raise the exception with an appropriate
        message.
        """
        requests_mock.get(
            DNB_UPDATES_URL,
            status_code=dnb_response_status,
        )

        with pytest.raises(DNBServiceError) as e:
            get_company_update_page(last_updated_after='foo')

        expected_message = f'DNB service returned an error status: {dnb_response_status}'

        assert e.value.args[0] == expected_message
        assert len(caplog.records) == 1
        assert caplog.records[0].getMessage() == expected_message

    @pytest.mark.parametrize(
        'request_exception, expected_exception, expected_message',
        (
            (
                ConnectionError,
                DNBServiceConnectionError,
                'Encountered an error connecting to DNB service',
            ),
            (
                ConnectTimeout,
                DNBServiceConnectionError,
                'Encountered an error connecting to DNB service',
            ),
            (
                Timeout,
                DNBServiceTimeoutError,
                'Encountered a timeout interacting with DNB service',
            ),
            (
                ReadTimeout,
                DNBServiceTimeoutError,
                'Encountered a timeout interacting with DNB service',
            ),
        ),
    )
    def test_get_company_dnb_service_request_error(
        self,
        caplog,
        requests_mock,
        request_exception,
        expected_exception,
        expected_message,
    ):
        """
        Test if there is an error connecting to dnb-service, we log it and raise
        the exception with an appropriate message.
        """
        requests_mock.get(
            DNB_UPDATES_URL,
            exc=request_exception,
        )

        with pytest.raises(expected_exception) as excinfo:
            get_company_update_page(last_updated_after='foo')

        assert str(excinfo.value) == expected_message
        assert len(caplog.records) == 1
        assert caplog.records[0].getMessage() == expected_message


class TestRollbackDNBCompanyUpdate:
    """
    Test rollback_dnb_company_update utility function.
    """

    @pytest.mark.parametrize(
        'fields, expected_fields',
        (
            (None, ALL_DNB_UPDATED_MODEL_FIELDS),
            (['name'], ['name']),
        ),
    )
    def test_rollback(
        self,
        formatted_dnb_company,
        fields,
        expected_fields,
    ):
        """
        Test that rollback_dnb_company_update will roll back all DNB fields.
        """
        with reversion.create_revision():
            company = CompanyFactory(duns_number=formatted_dnb_company['duns_number'])

        original_company = Company.objects.get(id=company.id)

        update_company_from_dnb(
            company,
            formatted_dnb_company,
            update_descriptor='foo',
        )

        rollback_dnb_company_update(company, 'foo', fields_to_update=fields)

        company.refresh_from_db()
        for field in expected_fields:
            assert getattr(company, field) == getattr(original_company, field)

        latest_version = Version.objects.get_for_object(company)[0]
        assert latest_version.revision.comment == 'Reverted D&B update from: foo'

    @pytest.mark.parametrize(
        'update_comment, error_message',
        (
            ('foo', 'Revision with comment: foo is the base version.'),
            ('bar', 'Revision with comment: bar not found.'),
        ),
    )
    def test_rollback_error(
        self,
        formatted_dnb_company,
        update_comment,
        error_message,
    ):
        """
        Test that rollback_dnb_company_update will fail with the given error
        message when there is an issue in finding the version to revert to.
        """
        company = CompanyFactory(duns_number=formatted_dnb_company['duns_number'])

        update_company_from_dnb(
            company,
            formatted_dnb_company,
            update_descriptor='foo',
        )

        with pytest.raises(RevisionNotFoundError) as excinfo:
            rollback_dnb_company_update(company, update_comment)
            assert str(excinfo.value) == error_message


class TestFormatDNBCompany:
    """
    Tests for format_dnb_company function.
    """

    def test_turnover_usd(self, dnb_response_uk):
        """
        Test that the function returns `turnover`
        and `is_turnover_estimated` when `annual_sales`
        are in USD.
        """
        dnb_company = dnb_response_uk['results'][0]
        company = format_dnb_company(dnb_company)
        assert company['turnover'] == dnb_company['annual_sales']
        assert company['is_turnover_estimated'] == dnb_company['is_annual_sales_estimated']

    def test_turnover_non_usd(self, dnb_response_uk):
        """
        Test that the function does not return `turnover`
        and `is_turnover_estimated` when `annual_sales`
        are not in USD.
        """
        dnb_company = dnb_response_uk['results'][0]
        dnb_company['annual_sales_currency'] = 'GBP'
        company = format_dnb_company(dnb_company)
        assert company['turnover'] is None
        assert company['is_turnover_estimated'] is None


class TestRequestChange:
    """
    Tests for request_changes function.
    """

    @pytest.mark.parametrize(
        'change_request, dnb_response, datahub_response',
        (

            # All valid fields
            (
                # change_request
                {
                    'duns_number': '123456789',
                    'changes': {
                        'name': 'Foo Bar',
                        'trading_names': ['Foo Bar INC'],
                        'website': 'example.com',
                        'address': {
                            'line_1': '123 Fake Street',
                            'line_2': 'Foo',
                            'town': 'London',
                            'county': 'Greater London',
                            'postcode': 'W1 0TN',
                            'country': 'GB',
                        },
                        'number_of_employees': 100,
                        'turnover': 1000,
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
                        'address_postcode': 'W1 0TN',
                        'employee_number': 100,
                        'annual_sales': 1000,
                        'annual_sales_currency': 'GBP',
                    },
                },
                # datahub_response
                {
                    'duns_number': '123456789',
                    'id': '11111111-2222-3333-4444-555555555555',
                    'status': 'pending',
                    'created_on': '2020-01-05T11:00:00',
                    'changes': {
                        'name': 'Foo Bar',
                        'trading_names': ['Foo Bar INC'],
                        'website': 'https://example.com',
                        'address': {
                            'line_1': '123 Fake Street',
                            'line_2': 'Foo',
                            'town': 'London',
                            'county': 'Greater London',
                            'postcode': 'W1 0TN',
                            'country': 'GB',
                        },
                        'number_of_employees': 100,
                        'turnover': 1000,
                        'turnover_currency': 'GBP',
                    },
                },
            ),

            # No address fields
            (
                # change_request
                {
                    'duns_number': '123456789',
                    'changes': {
                        'website': 'example.com',
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
                        'website': 'https://example.com',
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
                        'website': 'https://example.com',
                    },
                },
            ),

        ),
    )
    def test_valid(
        self,
        requests_mock,
        change_request,
        dnb_response,
        datahub_response,
    ):
        """
        The function should return 200 as well as a valid response
        when it is hit with a valid payload.
        """
        CompanyFactory(duns_number='123456789')

        requests_mock.post(
            DNB_CHANGE_REQUEST_URL,
            status_code=status.HTTP_201_CREATED,
            json=dnb_response,
        )

        response = request_changes(**change_request)

        assert response == datahub_response

    @pytest.mark.parametrize(
        'dnb_response_status',
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
        caplog,
        requests_mock,
        dnb_response_status,
    ):
        """
        The  endpoint should return 502 if the upstream
        `dnb-service` returns an error.
        """
        CompanyFactory(duns_number='123456789')
        requests_mock.post(
            DNB_CHANGE_REQUEST_URL,
            status_code=dnb_response_status,
        )

        with pytest.raises(DNBServiceError) as e:
            request_changes(
                '123456789',
                {'website': 'www.example.com'},
            )

        expected_message = f'DNB service returned an error status: {dnb_response_status}'

        assert e.value.args[0] == expected_message
        assert len(caplog.records) == 1
        assert caplog.records[0].getMessage() == expected_message

    @pytest.mark.parametrize(
        'request_exception, expected_exception, expected_message',
        (
            (
                ConnectionError,
                DNBServiceConnectionError,
                'Encountered an error connecting to DNB service',
            ),
            (
                ConnectTimeout,
                DNBServiceConnectionError,
                'Encountered an error connecting to DNB service',
            ),
            (
                Timeout,
                DNBServiceTimeoutError,
                'Encountered a timeout interacting with DNB service',
            ),
            (
                ReadTimeout,
                DNBServiceTimeoutError,
                'Encountered a timeout interacting with DNB service',
            ),
        ),
    )
    def test_request_error(
        self,
        caplog,
        requests_mock,
        request_exception,
        expected_exception,
        expected_message,
    ):
        """
        Test if there is an error connecting to dnb-service, we log it and raise the
        exception with an appropriate message.
        """
        requests_mock.post(
            DNB_CHANGE_REQUEST_URL,
            exc=request_exception,
        )

        with pytest.raises(expected_exception) as e:
            request_changes(
                '123456789',
                {'website': 'www.example.com'},
            )

        assert e.value.args[0] == expected_message
        assert len(caplog.records) == 1
        assert caplog.records[0].getMessage() == expected_message

    @override_settings(DNB_SERVICE_BASE_URL=None)
    def test_no_dnb_setting(self):
        """
        Test that we get an ImproperlyConfigured exception when the DNB_SERVICE_BASE_URL setting
        is not set.
        """
        with pytest.raises(ImproperlyConfigured):
            request_changes('123456789', {})
