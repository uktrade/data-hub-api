from unittest.mock import MagicMock, patch
from urllib.parse import urljoin
from uuid import UUID

import pytest
import reversion

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.test.utils import override_settings
from django.utils.timezone import now
from faker import Faker
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
from datahub.company.test.factories import (
    AdviserFactory,
    CompanyFactory,
    CompanyWithAreaFactory,
)
from datahub.dnb_api.constants import ALL_DNB_UPDATED_MODEL_FIELDS
from datahub.dnb_api.test.utils import model_to_dict_company
from datahub.dnb_api.utils import (
    create_company_hierarchy_dataframe,
    create_related_company_dataframe,
    DNBServiceConnectionError,
    DNBServiceError,
    DNBServiceInvalidRequestError,
    DNBServiceInvalidResponseError,
    DNBServiceTimeoutError,
    format_dnb_company,
    get_company,
    get_company_hierarchy_data,
    get_company_update_page,
    load_datahub_details,
    RevisionNotFoundError,
    rollback_dnb_company_update,
    update_company_from_dnb,
)
from datahub.metadata.models import AdministrativeArea, Country

pytestmark = pytest.mark.django_db

DNB_V2_SEARCH_URL = urljoin(f'{settings.DNB_SERVICE_BASE_URL}/', 'v2/companies/search/')
DNB_UPDATES_URL = urljoin(f'{settings.DNB_SERVICE_BASE_URL}/', 'companies/')
DNB_HIERARCHY_SEARCH_URL = urljoin(
    f'{settings.DNB_SERVICE_BASE_URL}/',
    'companies/hierarchy/search/',
)


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
        DNB_V2_SEARCH_URL,
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
            'DNB service unavailable',
        ),
        (
            ConnectTimeout,
            DNBServiceConnectionError,
            'DNB service unavailable',
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
        DNB_V2_SEARCH_URL,
        exc=request_exception,
    )

    with pytest.raises(expected_exception) as e:
        get_company('123456789')

    assert str(e.value) == str(expected_message)


@pytest.mark.parametrize(
    'search_results, expected_exception, expected_message',
    (
        (
            [],
            DNBServiceInvalidRequestError,
            'Cannot find a company with duns_number: 123456789',
        ),
        (
            ['foo', 'bar'],
            DNBServiceInvalidResponseError,
            'Multiple companies found with duns_number: 123456789',
        ),
        (
            [{'duns_number': '012345678'}],
            DNBServiceInvalidResponseError,
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
        DNB_V2_SEARCH_URL,
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
        DNB_V2_SEARCH_URL,
        json=dnb_response_uk,
    )

    dnb_company = get_company('123456789')

    assert dnb_company == {
        'company_number': '01261539',
        'name': 'FOO BICYCLE LIMITED',
        'duns_number': '123456789',
        'trading_names': [],
        'address': {
            'area': None,
            'country': UUID('80756b9a-5d95-e211-a939-e4115bead28a'),
            'county': '',
            'line_1': 'Unit 10, Ockham Drive',
            'line_2': '',
            'postcode': 'UB6 0F2',
            'town': 'GREENFORD',
        },
        'registered_address': {
            'area': None,
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
        formatted_dnb_company_area,
        base_company_dict,
        adviser_callable,
        update_descriptor,
    ):
        """
        Test that update_company_from_dnb will update all fields when the fields
        kwarg is not specified.
        """
        duns_number = '123456789'
        company = CompanyWithAreaFactory(duns_number=duns_number, pending_dnb_investigation=True)
        original_company = Company.objects.get(id=company.id)
        adviser = adviser_callable()
        update_company_from_dnb(
            company,
            formatted_dnb_company_area,
            user=adviser,
            update_descriptor=update_descriptor,
        )
        company.refresh_from_db()
        uk_country = Country.objects.get(iso_alpha2_code='GB')
        assert model_to_dict_company(company) == {
            **base_company_dict,
            'address_1': 'Unit 10, Ockham Drive',
            'address_2': '',
            'address_country': uk_country.id,
            'address_county': '',
            'address_area': AdministrativeArea.objects.get(area_code='TX').id,
            'address_postcode': 'UB6 0F2',
            'address_town': 'GREENFORD',
            'archived_documents_url_path': original_company.archived_documents_url_path,
            'business_type': original_company.business_type.id,
            'company_number': '01261539',
            'created_by': original_company.created_by.id,
            'duns_number': '123456789',
            'employee_range': original_company.employee_range.id,
            'export_experience_category': original_company.export_experience_category.id,
            'global_ultimate_duns_number': '291332174',
            'id': original_company.id,
            'is_number_of_employees_estimated': True,
            'modified_by': adviser.id if adviser else original_company.modified_by.id,
            'name': 'FOO BICYCLE LIMITED',
            'number_of_employees': 260,
            'sector': original_company.sector.id,
            'export_segment': original_company.export_segment,
            'export_sub_segment': original_company.export_sub_segment,
            'turnover': 50651895,
            'turnover_range': original_company.turnover_range.id,
            'uk_region': original_company.uk_region.id,
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
        'last_updated_after',
        (
            '2019-11-11T12:00:00',
            '2019-11-11',
        ),
    )
    @pytest.mark.parametrize(
        'next_page',
        (
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
                'DNB service unavailable',
            ),
            (
                ConnectTimeout,
                DNBServiceConnectionError,
                'DNB service unavailable',
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
        formatted_dnb_company_area,
        fields,
        expected_fields,
    ):
        """
        Test that rollback_dnb_company_update will roll back all DNB fields.
        """
        with reversion.create_revision():
            company = CompanyWithAreaFactory(
                duns_number=formatted_dnb_company_area['duns_number'],
            )

        original_company = Company.objects.get(id=company.id)

        update_company_from_dnb(
            company,
            formatted_dnb_company_area,
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


class TestDNBHierarchyData:
    """
    Tests for DNB Hierarchy function.
    """

    VALID_DUNS_NUMBER = '123456789'
    FAMILY_TREE_CACHE_KEY = f'family_tree_{VALID_DUNS_NUMBER}'

    @override_settings(DNB_SERVICE_BASE_URL=None)
    def test_dnb_hierarchy_improperly_configured_url_error(self):
        """
        Test that we get an ImproperlyConfigured exception when the DNB_SERVICE_BASE_URL setting
        is not set.
        """
        with pytest.raises(ImproperlyConfigured):
            get_company_hierarchy_data('123456789')

    @pytest.mark.usefixtures('local_memory_cache')
    def test_when_dnb_data_not_in_cache_dnb_api_is_called(self, requests_mock):
        """
        Test when the dnb family tree data is missing from the cache, a call is made to the dnb
        api to get the data and saved into the cache
        """
        matcher = requests_mock.post(
            DNB_HIERARCHY_SEARCH_URL,
            status_code=200,
            content=b'{"family_tree_members":[]}',
        )
        get_company_hierarchy_data(self.VALID_DUNS_NUMBER)

        assert matcher.called_once
        assert cache.get(self.FAMILY_TREE_CACHE_KEY) is not None

    @pytest.mark.usefixtures('local_memory_cache')
    def test_when_called_multiple_times_only_first_call_makes_an_api_call_to_dnb(
        self,
        requests_mock,
    ):
        """
        Test that after a successful call to the dnb api, all subsequent calls to the
        get_company_hierarchy_data function get the data from the cache
        """
        matcher = requests_mock.post(
            DNB_HIERARCHY_SEARCH_URL,
            status_code=200,
            content=b'{"family_tree_members":[]}',
        )

        get_company_hierarchy_data(self.VALID_DUNS_NUMBER)
        get_company_hierarchy_data(self.VALID_DUNS_NUMBER)
        get_company_hierarchy_data(self.VALID_DUNS_NUMBER)

        assert matcher.called_once

    @pytest.mark.usefixtures('local_memory_cache')
    def test_when_dnb_data_in_cache_this_is_returned_instead_of_calling_api(self, requests_mock):
        """
        Test when a value is stored in the cache the dnb api is not called
        """
        cache.set(self.FAMILY_TREE_CACHE_KEY, 'cached')

        matcher = requests_mock.post(
            DNB_HIERARCHY_SEARCH_URL,
            status_code=200,
            content=b'{"family_tree_members":[]}',
        )

        result = get_company_hierarchy_data(self.VALID_DUNS_NUMBER)
        assert result == 'cached'

        get_company_hierarchy_data(self.VALID_DUNS_NUMBER)
        get_company_hierarchy_data(self.VALID_DUNS_NUMBER)

        assert not matcher.called

    @pytest.mark.usefixtures('local_memory_cache')
    @pytest.mark.parametrize(
        'request_exception,expected_exception',
        (
            (
                ConnectionError,
                DNBServiceConnectionError,
            ),
            (
                ConnectTimeout,
                DNBServiceConnectionError,
            ),
            (
                Timeout,
                DNBServiceTimeoutError,
            ),
            (
                ReadTimeout,
                DNBServiceTimeoutError,
            ),
        ),
    )
    def test_when_dnb_api_error_response_is_not_cached(
        self,
        requests_mock,
        request_exception,
        expected_exception,
    ):
        """
        Test when the dnb api doesn't return a success http status code the value is not cached
        """
        with pytest.raises(expected_exception):
            requests_mock.post(DNB_HIERARCHY_SEARCH_URL, exc=request_exception)
            get_company_hierarchy_data(self.VALID_DUNS_NUMBER)
        assert cache.get(self.FAMILY_TREE_CACHE_KEY) is None


class TestCompanyHierarchyDataframe:
    def test_single_company_with_nested_opensearch_field_is_null(self, opensearch_with_signals):
        """
        Test when a single company contains a nested field in opensearch that is null the
        datatable is created with the correct column value
        """
        faker = Faker()

        ultimate_company_dnb = {
            'duns': '987654321',
            'primaryName': faker.company(),
            'corporateLinkage': {'hierarchyLevel': 1},
        }

        CompanyFactory(
            duns_number=ultimate_company_dnb['duns'],
            name=ultimate_company_dnb['primaryName'],
            uk_region_id=None,
        )

        tree_members = [ultimate_company_dnb]

        opensearch_with_signals.indices.refresh()
        df = create_company_hierarchy_dataframe(tree_members)

        assert df['ukRegion'][0] is None

    def test_single_company_with_deeply_nested_opensearch_field_is_null(
        self,
        opensearch_with_signals,
    ):
        """
        Test when a single company contains a deeply nested field in opensearch that is null the
        datatable is created with the correct column value
        """
        faker = Faker()

        ultimate_company_dnb = {
            'duns': '987654321',
            'primaryName': faker.company(),
            'corporateLinkage': {'hierarchyLevel': 1},
        }

        CompanyFactory(
            duns_number=ultimate_company_dnb['duns'],
            name=ultimate_company_dnb['primaryName'],
            address_country_id=None,
        )

        tree_members = [ultimate_company_dnb]

        opensearch_with_signals.indices.refresh()
        df = create_company_hierarchy_dataframe(tree_members)
        assert df['address'][0]['country'] is None

    def test_multiple_companies_with_nested_opensearch_field_combination_of_null_and_not_null(
        self,
        opensearch_with_signals,
    ):
        """
        Test when a multiple companies are returned from an opensearch query, that contain a
        nested field where some companies have a null value but other companies have a populated
        value, the datatable is created with the correct column value for each company
        """
        faker = Faker()

        ultimate_company_dnb = {
            'duns': '987654321',
            'primaryName': faker.company(),
            'corporateLinkage': {'hierarchyLevel': 1},
        }
        tree_member_level_2 = {
            'duns': '123456789',
            'primaryName': faker.company(),
            'corporateLinkage': {
                'hierarchyLevel': 2,
                'parent': {'duns': ultimate_company_dnb['duns']},
            },
        }

        CompanyFactory(
            duns_number=ultimate_company_dnb['duns'],
            name=ultimate_company_dnb['primaryName'],
            uk_region_id=None,
        )

        child_company = CompanyFactory(
            duns_number=tree_member_level_2['duns'],
            name=tree_member_level_2['primaryName'],
        )

        tree_members = [ultimate_company_dnb, tree_member_level_2]

        opensearch_with_signals.indices.refresh()
        df = create_company_hierarchy_dataframe(tree_members)

        assert df['ukRegion'][0] is None
        assert df['ukRegion'][1] == {
            'id': str(child_company.uk_region.id),
            'name': child_company.uk_region.name,
        }

    def test_multiple_companies_with_deeply_nested_opensearch_field_combination_of_null__not_null(
        self,
        opensearch_with_signals,
    ):
        """
        Test when a multiple companies are returned from an opensearch query, that contain a
        deeply nested field where some companies have a null value but other companies have a
        populated value, the datatable is created with the correct column value for each company
        """
        faker = Faker()

        ultimate_company_dnb = {
            'duns': '987654321',
            'primaryName': faker.company(),
            'corporateLinkage': {'hierarchyLevel': 1},
        }
        tree_member_level_2 = {
            'duns': '123456789',
            'primaryName': faker.company(),
            'corporateLinkage': {
                'hierarchyLevel': 2,
                'parent': {'duns': ultimate_company_dnb['duns']},
            },
        }

        CompanyFactory(
            duns_number=ultimate_company_dnb['duns'],
            name=ultimate_company_dnb['primaryName'],
            address_country_id=None,
        )

        child_company = CompanyFactory(
            duns_number=tree_member_level_2['duns'],
            name=tree_member_level_2['primaryName'],
        )

        tree_members = [ultimate_company_dnb, tree_member_level_2]

        opensearch_with_signals.indices.refresh()
        df = create_company_hierarchy_dataframe(tree_members)

        assert df['address'][0]['country'] is None
        assert df['address'][1]['country']['id'] == child_company.address_country_id

    @patch('datahub.dnb_api.utils.execute_search_query')
    def test_load_opensearch_request_above_max_duns_number_batches_requests(
        self,
        mocked_search_entity,
        opensearch_with_signals,
    ):
        mocked_search_entity.return_value = MagicMock()
        opensearch_with_signals.indices.refresh()

        duns_numbers = [str('111111111') for _ in range(0, 3100)]
        load_datahub_details(duns_numbers)

        assert mocked_search_entity.call_count == 4


class TestRelatedCompanyDataframe:
    def test_multiple_companies_both_directly_and_indirectly_related(
        self,
        opensearch_with_signals,
    ):
        """
        Test when a dataframe is created using multiple companies where the parent
        relationship is both directly linked and indirectly linked value, the datatable
        is created with the correct column value for each company
        """
        faker = Faker()

        ultimate_company_dnb = {
            'duns': '113456789',
            'primaryName': faker.company(),
            'corporateLinkage': {'hierarchyLevel': 1},
        }
        parent_company_dnb = {
            'duns': '223456789',
            'primaryName': faker.company(),
            'corporateLinkage': {
                'hierarchyLevel': 2,
                'parent': {'duns': ultimate_company_dnb['duns']},
            },
        }
        child_one_company_dnb = {
            'duns': '333456789',
            'primaryName': faker.company(),
            'corporateLinkage': {
                'hierarchyLevel': 2,
                'parent': {'duns': parent_company_dnb['duns']},
            },
        }
        child_two_company_dnb = {
            'duns': '443456789',
            'primaryName': faker.company(),
            'corporateLinkage': {
                'hierarchyLevel': 2,
                'parent': {'duns': parent_company_dnb['duns']},
            },
        }
        unrelated_company_dnb = {
            'duns': '553456789',
            'primaryName': faker.company(),
            'corporateLinkage': {
                'hierarchyLevel': 2,
                'parent': {'duns': ultimate_company_dnb['duns']},
            },
        }

        tree_members = [
            ultimate_company_dnb,
            parent_company_dnb,
            child_one_company_dnb,
            child_two_company_dnb,
            unrelated_company_dnb,
        ]

        opensearch_with_signals.indices.refresh()

        df = create_related_company_dataframe(tree_members)

        assert df['duns'][0] == ultimate_company_dnb['duns']
        assert df['duns'][1] == parent_company_dnb['duns']
        assert df['duns'][2] == child_one_company_dnb['duns']
        assert df['duns'][3] == child_two_company_dnb['duns']
        assert df['duns'][4] == unrelated_company_dnb['duns']
        assert df['corporateLinkage.parent.duns'][0] is None
        assert df['corporateLinkage.parent.duns'][1] == ultimate_company_dnb['duns']
        assert df['corporateLinkage.parent.duns'][2] == parent_company_dnb['duns']
        assert df['corporateLinkage.parent.duns'][3] == parent_company_dnb['duns']
        assert df['corporateLinkage.parent.duns'][4] == ultimate_company_dnb['duns']

    def test_none_returned_from_empty_tree_members(
        self,
        opensearch_with_signals,
    ):
        """
        Test when a dataframe is created using multiple companies where the parent
        relationship is both directly linked and indirectly linked value, the datatable
        is created with the correct column value for each company
        """
        faker = Faker()

        ultimate_company_dnb = {
            'duns': '113456789',
            'primaryName': faker.company(),
            'corporateLinkage': {'hierarchyLevel': 1},
        }

        tree_members = [ultimate_company_dnb]

        opensearch_with_signals.indices.refresh()
        df = create_related_company_dataframe(tree_members)

        assert df['corporateLinkage.parent.duns'][0] is None
