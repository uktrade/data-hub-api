from urllib.parse import urljoin
from uuid import UUID

import pytest
from django.conf import settings
from django.forms.models import model_to_dict
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
from datahub.dnb_api.utils import (
    DNBServiceConnectionError,
    DNBServiceError,
    DNBServiceInvalidRequest,
    DNBServiceInvalidResponse,
    DNBServiceTimeoutError,
    format_dnb_company,
    get_company,
    get_company_update_page,
    update_company_from_dnb,
)
from datahub.metadata.models import Country

pytestmark = pytest.mark.django_db


DNB_SEARCH_URL = urljoin(f'{settings.DNB_SERVICE_BASE_URL}/', 'companies/search/')
DNB_UPDATES_URL = urljoin(f'{settings.DNB_SERVICE_BASE_URL}/', 'companies/')


@pytest.fixture
def formatted_dnb_company(dnb_response_uk):
    """
    Get formatted DNB company data.
    """
    return format_dnb_company(dnb_response_uk['results'][0])


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
    dnb_company_search_feature_flag,
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
    dnb_company_search_feature_flag,
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
    dnb_company_search_feature_flag,
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
    dnb_company_search_feature_flag,
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
        dnb_company_search_feature_flag,
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
        assert model_to_dict(company) == {
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
            'registered_address_1': 'C/O LONE VARY',
            'registered_address_2': '',
            'registered_address_country': uk_country.id,
            'registered_address_county': '',
            'registered_address_postcode': 'UB6 0F2',
            'registered_address_town': 'GREENFORD',
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
            'website': 'http://foo.com',
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
        dnb_company_search_feature_flag,
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
        dnb_company_search_feature_flag,
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
        'cursor', (
            None,
            'some-cursor',
        ),
    )
    def test_valid(self, requests_mock, last_updated_after, cursor):
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
            DNB_UPDATES_URL,
            status_code=status.HTTP_200_OK,
            json=expected_response,
        )
        response = get_company_update_page(last_updated_after, cursor)

        assert mocker.last_request.qs.get('last_updated_after') == [last_updated_after]
        assert mocker.last_request.qs.get('cursor') == [cursor or '']

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
