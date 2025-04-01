from unittest.mock import MagicMock, patch
from urllib.parse import urljoin
from uuid import UUID, uuid4

import pytest
import requests_mock
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
from datahub.core.constants import AdministrativeArea as AdministrativeAreaConstants
from datahub.core.constants import Country as CountryConstants
from datahub.core.exceptions import (
    APIBadRequestException,
    APINotFoundException,
)
from datahub.dnb_api.constants import ALL_DNB_UPDATED_MODEL_FIELDS
from datahub.dnb_api.test.utils import model_to_dict_company
from datahub.dnb_api.utils import (
    DNBServiceConnectionError,
    DNBServiceError,
    DNBServiceInvalidRequestError,
    DNBServiceInvalidResponseError,
    DNBServiceTimeoutError,
    RevisionNotFoundError,
    create_company_hierarchy_dataframe,
    create_company_tree,
    create_related_company_dataframe,
    format_company_for_family_tree,
    format_dnb_company,
    get_cached_dnb_company,
    get_company,
    get_company_hierarchy_count,
    get_company_update_page,
    get_full_company_hierarchy_data,
    get_reduced_company_hierarchy_data,
    load_datahub_details,
    rollback_dnb_company_update,
    update_company_from_dnb,
    validate_company_id,
)
from datahub.metadata.models import AdministrativeArea, Country

pytestmark = pytest.mark.django_db

DNB_V2_SEARCH_URL = urljoin(f'{settings.DNB_SERVICE_BASE_URL}/', 'v2/companies/search/')
DNB_UPDATES_URL = urljoin(f'{settings.DNB_SERVICE_BASE_URL}/', 'companies/')
DNB_HIERARCHY_SEARCH_URL = urljoin(
    f'{settings.DNB_SERVICE_BASE_URL}/',
    'companies/hierarchy/search/',
)
DNB_HIERARCHY_COUNT_URL = urljoin(DNB_HIERARCHY_SEARCH_URL, 'count')


class TestCompanySearch:
    @pytest.mark.parametrize(
        'dnb_response_status',
        [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_405_METHOD_NOT_ALLOWED,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ],
    )
    def test_get_company_dnb_service_error(
        self,
        caplog,
        requests_mock,
        dnb_response_status,
    ):
        """Test if the dnb-service returns a status code that is not
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
        ('request_exception', 'expected_exception', 'expected_message'),
        [
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
        ],
    )
    def test_get_company_dnb_service_request_error(
        self,
        caplog,
        requests_mock,
        request_exception,
        expected_exception,
        expected_message,
    ):
        """Test if there is an error connecting to dnb-service, we log it and raise the exception
        with an appropriate message.
        """
        requests_mock.post(
            DNB_V2_SEARCH_URL,
            exc=request_exception,
        )

        with pytest.raises(expected_exception) as e:
            get_company('123456789')

        assert str(e.value) == str(expected_message)

    @pytest.mark.parametrize(
        ('search_results', 'expected_exception', 'expected_message'),
        [
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
        ],
    )
    def test_get_company_invalid_request_response(
        self,
        caplog,
        requests_mock,
        search_results,
        expected_exception,
        expected_message,
    ):
        """Test if a given `duns_number` gets anything other than a single company
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
        self,
        caplog,
        requests_mock,
        dnb_response_uk,
    ):
        """Test if dnb-service returns a valid response, get_company
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
            'is_out_of_business': False,
        }


class TestUpdateCompanyFromDNB:
    """Test update_company_from_dnb utility function."""

    @pytest.mark.parametrize(
        'adviser_callable',
        [
            lambda: None,
            lambda: AdviserFactory(),
        ],
    )
    @pytest.mark.parametrize(
        'update_descriptor',
        [
            None,
            'automatic',
        ],
    )
    @freeze_time('2019-01-01 11:12:13')
    def test_update_company_from_dnb_all_fields(
        self,
        formatted_dnb_company_area_non_uk,
        base_company_dict,
        adviser_callable,
        update_descriptor,
    ):
        """Test that update_company_from_dnb will update all fields when the fields
        kwarg is not specified.

        Test with non-uk companies as UK companies do not have an AdministrativeArea.
        """
        duns_number = '123456789'
        company = CompanyWithAreaFactory(
            duns_number=duns_number,
            pending_dnb_investigation=True,
            strategy='ABC',
            address_area_id=AdministrativeAreaConstants.new_york.value.id,
            address_country_id=CountryConstants.united_states.value.id,
        )
        original_company = Company.objects.get(id=company.id)
        adviser = adviser_callable()
        update_company_from_dnb(
            company,
            formatted_dnb_company_area_non_uk,
            user=adviser,
            update_descriptor=update_descriptor,
        )
        company.refresh_from_db()

        us_country = Country.objects.get(iso_alpha2_code='US')

        assert model_to_dict_company(company) == {
            **base_company_dict,
            'address_1': '150 Madison Ave',
            'address_2': '',
            'address_country': us_country.id,
            'address_county': '',
            'address_area': AdministrativeArea.objects.get(
                country_id=us_country.id,
                name='New York',
            ).id,
            'address_postcode': '10033-1062',
            'address_town': 'New York',
            'archived_documents_url_path': original_company.archived_documents_url_path,
            'business_type': original_company.business_type.id,
            'trading_names': [
                'Acme',
            ],
            'created_by': original_company.created_by.id,
            'duns_number': '123456789',
            'employee_range': original_company.employee_range.id,
            'export_experience_category': original_company.export_experience_category.id,
            'global_ultimate_duns_number': '157270606',
            'id': original_company.id,
            'is_number_of_employees_estimated': False,
            'modified_by': adviser.id if adviser else original_company.modified_by.id,
            'name': 'Acme Corporation',
            'number_of_employees': 100,
            'sector': original_company.sector.id,
            'export_segment': original_company.export_segment,
            'export_sub_segment': original_company.export_sub_segment,
            'turnover': 1000000,
            'turnover_range': original_company.turnover_range.id,
            'uk_region': original_company.uk_region.id,
            'dnb_modified_on': now(),
            'strategy': 'ABC',
            'is_out_of_business': original_company.is_out_of_business,
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
        [
            lambda: None,
            lambda: AdviserFactory(),
        ],
    )
    def test_update_company_from_dnb_partial_fields_single(
        self,
        formatted_dnb_company,
        adviser_callable,
    ):
        """Test that update_company_from_dnb can update a subset of fields."""
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
        [
            lambda: None,
            lambda: AdviserFactory(),
        ],
    )
    def test_update_company_from_dnb_partial_fields_multiple(
        self,
        formatted_dnb_company,
        adviser_callable,
    ):
        """Test that update_company_from_dnb can update a subset of fields."""
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
        """Tests that ValidationError is raised when data returned by DNB is not valid for saving to a
        Data Hub Company.
        """
        company = CompanyFactory(duns_number='123456789')
        adviser = AdviserFactory()
        formatted_dnb_company['name'] = None
        with pytest.raises(serializers.ValidationError) as excinfo:  # noqa: PT012
            update_company_from_dnb(company, formatted_dnb_company, adviser)
            assert str(excinfo) == 'Data from D&B did not pass the Data Hub validation checks.'


class TestGetCompanyUpdatePage:
    """Test for the `get_company_update_page` utility function."""

    @pytest.mark.parametrize(
        'last_updated_after',
        [
            '2019-11-11T12:00:00',
            '2019-11-11',
        ],
    )
    @pytest.mark.parametrize(
        'next_page',
        [
            None,
            'http://some.url/endpoint?cursor=some-cursor',
        ],
    )
    def test_valid(self, requests_mock, last_updated_after, next_page):
        """Test if `get_company_update_page` returns the right response
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
        [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_405_METHOD_NOT_ALLOWED,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ],
    )
    def test_dnb_service_error(
        self,
        caplog,
        requests_mock,
        dnb_response_status,
    ):
        """Test if the dnb-service returns a status code that is not
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
        ('request_exception', 'expected_exception', 'expected_message'),
        [
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
        ],
    )
    def test_get_company_dnb_service_request_error(
        self,
        caplog,
        requests_mock,
        request_exception,
        expected_exception,
        expected_message,
    ):
        """Test if there is an error connecting to dnb-service, we log it and raise
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
    """Test rollback_dnb_company_update utility function."""

    @pytest.mark.parametrize(
        ('fields', 'expected_fields'),
        [
            (None, ALL_DNB_UPDATED_MODEL_FIELDS),
            (['name'], ['name']),
        ],
    )
    def test_rollback(
        self,
        formatted_dnb_company_area_non_uk,
        fields,
        expected_fields,
    ):
        """Test that rollback_dnb_company_update will roll back all DNB fields.
        Test with non-uk companies as UK companies do not have an AdministrativeArea.
        """
        with reversion.create_revision():
            company = CompanyWithAreaFactory(
                duns_number=formatted_dnb_company_area_non_uk['duns_number'],
                address_area_id=AdministrativeAreaConstants.new_york.value.id,
                address_country_id=CountryConstants.united_states.value.id,
            )

        original_company = Company.objects.get(id=company.id)

        update_company_from_dnb(
            company,
            formatted_dnb_company_area_non_uk,
            update_descriptor='foo',
        )

        rollback_dnb_company_update(company, 'foo', fields_to_update=fields)

        company.refresh_from_db()
        for field in expected_fields:
            assert getattr(company, field) == getattr(original_company, field)

        latest_version = Version.objects.get_for_object(company)[0]
        assert latest_version.revision.comment == 'Reverted D&B update from: foo'

    @pytest.mark.parametrize(
        ('update_comment', 'error_message'),
        [
            ('foo', 'Revision with comment: foo is the base version.'),
            ('bar', 'Revision with comment: bar not found.'),
        ],
    )
    def test_rollback_error(
        self,
        formatted_dnb_company,
        update_comment,
        error_message,
    ):
        """Test that rollback_dnb_company_update will fail with the given error
        message when there is an issue in finding the version to revert to.
        """
        company = CompanyFactory(duns_number=formatted_dnb_company['duns_number'])

        update_company_from_dnb(
            company,
            formatted_dnb_company,
            update_descriptor='foo',
        )

        with pytest.raises(RevisionNotFoundError) as excinfo:  # noqa: PT012
            rollback_dnb_company_update(company, update_comment)
            assert str(excinfo.value) == error_message


class TestFormatDNBCompany:
    """Tests for format_dnb_company function."""

    def test_turnover_usd(self, dnb_response_uk):
        """Test that the function returns `turnover`
        and `is_turnover_estimated` when `annual_sales`
        are in USD.
        """
        dnb_company = dnb_response_uk['results'][0]
        company = format_dnb_company(dnb_company)
        assert company['turnover'] == dnb_company['annual_sales']
        assert company['is_turnover_estimated'] == dnb_company['is_annual_sales_estimated']

    def test_turnover_non_usd(self, dnb_response_uk):
        """Test that the function does not return `turnover`
        and `is_turnover_estimated` when `annual_sales`
        are not in USD.
        """
        dnb_company = dnb_response_uk['results'][0]
        dnb_company['annual_sales_currency'] = 'GBP'
        company = format_dnb_company(dnb_company)
        assert company['turnover'] is None
        assert company['is_turnover_estimated'] is None


class TestDNBFullHierarchyData:
    """Tests for DNB Hierarchy function."""

    VALID_DUNS_NUMBER = '123456789'
    FAMILY_TREE_CACHE_KEY = f'family_tree_{VALID_DUNS_NUMBER}'

    @override_settings(DNB_SERVICE_BASE_URL=None)
    def test_dnb_hierarchy_improperly_configured_url_error(self):
        """Test that we get an ImproperlyConfigured exception when the DNB_SERVICE_BASE_URL setting
        is not set.
        """
        with pytest.raises(ImproperlyConfigured):
            get_full_company_hierarchy_data('123456789')

    @pytest.mark.usefixtures('local_memory_cache')
    def test_when_dnb_data_not_in_cache_dnb_api_is_called(self, requests_mock):
        """Test when the dnb family tree data is missing from the cache, a call is made to the dnb
        api to get the data and saved into the cache.
        """
        matcher = requests_mock.post(
            DNB_HIERARCHY_SEARCH_URL,
            status_code=200,
            content=b'{"family_tree_members":[]}',
        )
        get_full_company_hierarchy_data(self.VALID_DUNS_NUMBER)

        assert matcher.called_once
        assert cache.get(self.FAMILY_TREE_CACHE_KEY) is not None

    @pytest.mark.usefixtures('local_memory_cache')
    def test_when_called_multiple_times_only_first_call_makes_an_api_call_to_dnb(
        self,
        requests_mock,
    ):
        """Test that after a successful call to the dnb api, all subsequent calls to the
        get_full_company_hierarchy_data function get the data from the cache.
        """
        matcher = requests_mock.post(
            DNB_HIERARCHY_SEARCH_URL,
            content=b'{"family_tree_members":[]}',
        )

        get_full_company_hierarchy_data(self.VALID_DUNS_NUMBER)
        get_full_company_hierarchy_data(self.VALID_DUNS_NUMBER)
        get_full_company_hierarchy_data(self.VALID_DUNS_NUMBER)

        assert matcher.called_once

    @pytest.mark.usefixtures('local_memory_cache')
    def test_when_dnb_data_in_cache_this_is_returned_instead_of_calling_api(self, requests_mock):
        """Test when a value is stored in the cache the dnb api is not called."""
        cache.set(self.FAMILY_TREE_CACHE_KEY, 'cached')

        matcher = requests_mock.post(
            DNB_HIERARCHY_SEARCH_URL,
            content=b'{"family_tree_members":[]}',
        )

        result = get_full_company_hierarchy_data(self.VALID_DUNS_NUMBER)
        assert result == 'cached'

        get_full_company_hierarchy_data(self.VALID_DUNS_NUMBER)
        get_full_company_hierarchy_data(self.VALID_DUNS_NUMBER)

        assert not matcher.called

    @pytest.mark.usefixtures('local_memory_cache')
    @pytest.mark.parametrize(
        ('request_exception', 'expected_exception'),
        [
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
        ],
    )
    def test_when_dnb_api_error_response_is_not_cached(
        self,
        requests_mock,
        request_exception,
        expected_exception,
    ):
        """Test when the dnb api doesn't return a success http status code the value is not cached."""
        with pytest.raises(expected_exception):  # noqa: PT012
            requests_mock.post(DNB_HIERARCHY_SEARCH_URL, exc=request_exception)
            get_full_company_hierarchy_data(self.VALID_DUNS_NUMBER)
        assert cache.get(self.FAMILY_TREE_CACHE_KEY) is None

    def test_when_dnb_api_returns_status_code_not_success_response_is_not_cached(
        self,
        requests_mock,
    ):
        """Test when the dnb api doesn't return a success http status code the value is not cached."""
        with pytest.raises(DNBServiceError):  # noqa: PT012
            requests_mock.post(
                DNB_HIERARCHY_SEARCH_URL,
                status_code=500,
                content=b'{"family_tree_members":[]}',
            )
            get_full_company_hierarchy_data(self.VALID_DUNS_NUMBER)
        assert cache.get(self.FAMILY_TREE_CACHE_KEY) is None


class TestCompanyHierarchyDataframe:
    def test_single_company_with_nested_opensearch_field_is_null(self, opensearch_with_signals):
        """Test when a single company contains a nested field in opensearch that is null the
        datatable is created with the correct column value.
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
        df = create_company_hierarchy_dataframe(tree_members, ultimate_company_dnb['duns'])

        assert df['ukRegion'][0] is None

    def test_single_company_with_deeply_nested_opensearch_field_is_null(
        self,
        opensearch_with_signals,
    ):
        """Test when a single company contains a deeply nested field in opensearch that is null the
        datatable is created with the correct column value.
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
        df = create_company_hierarchy_dataframe(tree_members, ultimate_company_dnb['duns'])
        assert df['address'][0]['country'] is None

    def test_multiple_companies_with_nested_opensearch_field_combination_of_null_and_not_null(
        self,
        opensearch_with_signals,
    ):
        """Test when a multiple companies are returned from an opensearch query, that contain a
        nested field where some companies have a null value but other companies have a populated
        value, the datatable is created with the correct column value for each company.
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
        df = create_company_hierarchy_dataframe(tree_members, ultimate_company_dnb['duns'])

        assert df['ukRegion'][0] is None
        assert df['ukRegion'][1] == {
            'id': str(child_company.uk_region.id),
            'name': child_company.uk_region.name,
        }

    def test_multiple_companies_with_deeply_nested_opensearch_field_combination_of_null__not_null(
        self,
        opensearch_with_signals,
    ):
        """Test when a multiple companies are returned from an opensearch query, that contain a
        deeply nested field where some companies have a null value but other companies have a
        populated value, the datatable is created with the correct column value for each company.
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
        df = create_company_hierarchy_dataframe(tree_members, ultimate_company_dnb['duns'])

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
        """Test when a dataframe is created using multiple companies where the parent
        relationship is both directly linked and indirectly linked value, the datatable
        is created with the correct column value for each company.
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
        """Test when a dataframe is created using multiple companies where the parent
        relationship is both directly linked and indirectly linked value, the datatable
        is created with the correct column value for each company.
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


class TestDNBHierarchyCount:
    """Tests for DNB Hierarchy count function."""

    VALID_DUNS_NUMBER = '123456789'
    FAMILY_TREE_CACHE_KEY = f'family_tree_count_{VALID_DUNS_NUMBER}'

    @override_settings(DNB_SERVICE_BASE_URL=None)
    def test_dnb_hierarchy_count_improperly_configured_url_error(self):
        """Test that we get an ImproperlyConfigured exception when the DNB_SERVICE_BASE_URL setting
        is not set.
        """
        with pytest.raises(ImproperlyConfigured):
            get_company_hierarchy_count('123456789')

    @pytest.mark.usefixtures('local_memory_cache')
    def test_when_dnb_data_not_in_cache_dnb_api_is_called(self, requests_mock):
        """Test when the dnb family tree count is missing from the cache, a call is made to the dnb
        api to get the count and saved into the cache.
        """
        matcher = requests_mock.post(
            DNB_HIERARCHY_COUNT_URL,
            content=b'1',
        )
        get_company_hierarchy_count(self.VALID_DUNS_NUMBER)

        assert matcher.called_once
        assert cache.get(self.FAMILY_TREE_CACHE_KEY) is not None

    @pytest.mark.usefixtures('local_memory_cache')
    def test_when_called_multiple_times_only_first_call_makes_an_api_call_to_dnb(
        self,
        requests_mock,
    ):
        """Test that after a successful call to the dnb api, all subsequent calls to the
        get_company_hierarchy_count function get the data from the cache.
        """
        matcher = requests_mock.post(
            DNB_HIERARCHY_COUNT_URL,
            content=b'5',
        )

        get_company_hierarchy_count(self.VALID_DUNS_NUMBER)
        get_company_hierarchy_count(self.VALID_DUNS_NUMBER)
        get_company_hierarchy_count(self.VALID_DUNS_NUMBER)

        assert matcher.called_once

    @pytest.mark.usefixtures('local_memory_cache')
    def test_when_dnb_data_in_cache_this_is_returned_instead_of_calling_api(self, requests_mock):
        """Test when a value is stored in the cache the dnb api is not called."""
        cache.set(self.FAMILY_TREE_CACHE_KEY, 'cached')

        matcher = requests_mock.post(
            DNB_HIERARCHY_COUNT_URL,
            content=b'1',
        )

        result = get_company_hierarchy_count(self.VALID_DUNS_NUMBER)
        assert result == 'cached'

        get_company_hierarchy_count(self.VALID_DUNS_NUMBER)
        get_company_hierarchy_count(self.VALID_DUNS_NUMBER)

        assert not matcher.called

    @pytest.mark.usefixtures('local_memory_cache')
    @pytest.mark.parametrize(
        ('request_exception', 'expected_exception'),
        [
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
        ],
    )
    def test_when_dnb_api_error_response_is_not_cached(
        self,
        requests_mock,
        request_exception,
        expected_exception,
    ):
        """Test when the dnb api raises an error the value is not cached."""
        with pytest.raises(expected_exception):  # noqa: PT012
            requests_mock.post(DNB_HIERARCHY_COUNT_URL, exc=request_exception)
            get_company_hierarchy_count(self.VALID_DUNS_NUMBER)
        assert cache.get(self.FAMILY_TREE_CACHE_KEY) is None

    def test_when_dnb_api_returns_status_code_not_success_response_is_not_cached(
        self,
        requests_mock,
    ):
        """Test when the dnb api doesn't return a success http status code the value is not cached."""
        with pytest.raises(DNBServiceError):  # noqa: PT012
            requests_mock.post(
                DNB_HIERARCHY_COUNT_URL,
                status_code=500,
                content=b'2',
            )
            get_company_hierarchy_count(self.VALID_DUNS_NUMBER)
        assert cache.get(self.FAMILY_TREE_CACHE_KEY) is None


class TestReducedHierarchyData:
    def test_when_no_duns_number_provided_empty_array_returned(self):
        """Test when no duns number is provided an empty array of hierarchy data is returned."""
        assert get_reduced_company_hierarchy_data(duns_number='').data == []

    def test_when_company_has_no_parent_1_company_returned(self, requests_mock):
        """Test when a company has no parent only that company is returned."""
        requests_mock.post(
            DNB_V2_SEARCH_URL,
            status_code=200,
            json={'results': [{'duns_number': '123456789', 'primary_name': 'ABC'}]},
        )

        hierarchy_data = get_reduced_company_hierarchy_data('123456789').data[0]
        assert hierarchy_data['corporateLinkage.parent.duns'] is None
        assert hierarchy_data['duns'] == '123456789'

    @pytest.mark.usefixtures('local_memory_cache')
    def test_when_company_has_3_parents_all_4_companies_are_returned(self):
        """Test when a company has 3 levels of parents above them, all 4 companies are returned in
        the hierarchy data.
        """
        responses = [
            {
                'status_code': 200,
                'json': {
                    'results': [
                        {
                            'duns_number': '111111111',
                            'parent_duns_number': '222222222',
                            'primary_name': 'DEF',
                        },
                    ],
                },
            },
            {
                'status_code': 200,
                'json': {
                    'results': [{'duns_number': '222222222', 'parent_duns_number': '333333333'}],
                },
            },
            {
                'status_code': 200,
                'json': {
                    'results': [{'duns_number': '333333333', 'parent_duns_number': '444444444'}],
                },
            },
            {
                'status_code': 200,
                'json': {'results': [{'duns_number': '444444444', 'parent_duns_number': ''}]},
            },
        ]
        with requests_mock.Mocker() as m:
            m.post(DNB_V2_SEARCH_URL, responses)

            hierarchy_data = get_reduced_company_hierarchy_data('111111111')
            assert hierarchy_data.count == 4
            assert hierarchy_data.data[0]['corporateLinkage.hierarchyLevel'] == 4
            assert hierarchy_data.data[1]['corporateLinkage.hierarchyLevel'] == 3
            assert hierarchy_data.data[2]['corporateLinkage.hierarchyLevel'] == 2
            assert hierarchy_data.data[3]['corporateLinkage.hierarchyLevel'] == 1


class TestCompanyCaching:
    VALID_DUNS_NUMBER = '123456789'
    COMPANY_CACHE_KEY = f'dnb_company_{VALID_DUNS_NUMBER}'

    @pytest.mark.usefixtures('local_memory_cache')
    def test_when_company_data_not_in_cache_dnb_api_is_called(self, requests_mock):
        """Test when the dnb company data is missing from the cache, a call is made to the dnb
        api to get the data and saved into the cache.
        """
        matcher = requests_mock.post(
            DNB_V2_SEARCH_URL,
            json={'results': [{'duns_number': self.VALID_DUNS_NUMBER}]},
        )
        get_cached_dnb_company(self.VALID_DUNS_NUMBER)

        assert matcher.called_once
        assert cache.get(self.COMPANY_CACHE_KEY) is not None

    @pytest.mark.usefixtures('local_memory_cache')
    def test_when_called_multiple_times_only_first_call_makes_an_api_call_to_dnb(
        self,
        requests_mock,
    ):
        """Test that after a successful call to the dnb api, all subsequent calls to the
        get_cached_company function get the data from the cache.
        """
        matcher = requests_mock.post(
            DNB_V2_SEARCH_URL,
            json={'results': [{'duns_number': self.VALID_DUNS_NUMBER}]},
        )

        get_cached_dnb_company(self.VALID_DUNS_NUMBER)
        get_cached_dnb_company(self.VALID_DUNS_NUMBER)
        get_cached_dnb_company(self.VALID_DUNS_NUMBER)

        assert matcher.called_once


class TestFormatCompanyForFamilyTree:
    def test_no_company_returns_empty_object(self):
        """Test when the company provided is none, an object is still returned."""
        assert format_company_for_family_tree(None) == {
            'duns': None,
            'corporateLinkage.parent.duns': None,
            'primaryName': None,
        }

    def test_company_with_no_parent_duns_returns_none_for_corporate_linkage_parent(self):
        """Test a company without a parent duns number returns none for the corporate linkage."""
        assert format_company_for_family_tree({'duns_number': '1', 'primary_name': 'abc'}) == {
            'duns': '1',
            'corporateLinkage.parent.duns': None,
            'primaryName': 'abc',
        }

    def test_company_with_parent_duns_returns_id_for_corporate_linkage_parent(self):
        """Test a company with a parent duns number returns that number for the corporate linkage."""
        assert format_company_for_family_tree(
            {'duns_number': '1', 'parent_duns_number': '2', 'primary_name': 'abc'},
        ) == {
            'duns': '1',
            'corporateLinkage.parent.duns': '2',
            'primaryName': 'abc',
        }


class TestValidateCompanyId:
    def test_company_id_is_valid(self):
        with pytest.raises(APIBadRequestException):
            validate_company_id('11223344')

    def test_company_has_no_company_id(self):
        with pytest.raises(APINotFoundException):
            validate_company_id(uuid4())

    def test_company_has_no_duns_number(self):
        company = CompanyFactory(duns_number=None)
        with pytest.raises(APIBadRequestException):
            validate_company_id(company.id)

    def test_company_has_invalid_duns_number(self):
        company = CompanyFactory(duns_number='123')
        with pytest.raises(serializers.ValidationError):
            validate_company_id(company.id)


class TestCreateCompanyTree:
    def test_ultimate_parent_company_subsidiaries_left_unchanged_when_it_is_the_requested_company(
        self,
        opensearch_with_signals,
    ):
        """When a requested company is the ultimate parent, no changes should be made to the
        subsidiaries.
        """
        faker = Faker()

        ultimate_company = {
            'duns': '000000000',
            'primaryName': faker.company(),
            'corporateLinkage': {'hierarchyLevel': 1},
        }
        ultimate_company_subsidiary_company_1 = {
            'duns': '111111111',
            'primaryName': faker.company(),
            'corporateLinkage': {
                'hierarchyLevel': 2,
                'parent': {'duns': ultimate_company['duns']},
            },
        }

        tree = create_company_tree(
            [
                ultimate_company,
                ultimate_company_subsidiary_company_1,
            ],
            ultimate_company['duns'],
        )

        assert (
            tree['subsidiaries'][0]['duns_number'] == ultimate_company_subsidiary_company_1['duns']
        )

    def test_parent_company_subsidiaries_left_unchanged_when_it_is_the_requested_company(
        self,
        opensearch_with_signals,
    ):
        """When a requested company is a parent with subsidaries and no siblings, no changes should
        be made to the subsidiaries.
        """
        faker = Faker()

        ultimate_company = {
            'duns': '000000000',
            'primaryName': faker.company(),
            'corporateLinkage': {'hierarchyLevel': 1},
        }
        ultimate_company_subsidiary_company_1 = {
            'duns': '111111111',
            'primaryName': faker.company(),
            'corporateLinkage': {
                'hierarchyLevel': 2,
                'parent': {'duns': ultimate_company['duns']},
            },
        }
        subsidiary_company_1_subsidiary_company_1 = {
            'duns': '222222222',
            'primaryName': faker.company(),
            'corporateLinkage': {
                'hierarchyLevel': 3,
                'parent': {'duns': ultimate_company_subsidiary_company_1['duns']},
            },
        }

        tree = create_company_tree(
            [
                ultimate_company,
                ultimate_company_subsidiary_company_1,
                subsidiary_company_1_subsidiary_company_1,
            ],
            ultimate_company_subsidiary_company_1['duns'],
        )

        assert (
            tree['subsidiaries'][0]['duns_number'] == ultimate_company_subsidiary_company_1['duns']
        )

    def test_subsidiary_company_at_start_of_list_is_left_in_place_when_it_is_the_requested_company(
        self,
        opensearch_with_signals,
    ):
        """When a requested company is a subsidiary company in the tree, and it is already the first
        company in the list, check it remains at the start of the list.
        """
        faker = Faker()

        ultimate_company = {
            'duns': '000000000',
            'primaryName': faker.company(),
            'corporateLinkage': {'hierarchyLevel': 1},
        }
        ultimate_company_subsidiary_company_1 = {
            'duns': '111111111',
            'primaryName': faker.company(),
            'corporateLinkage': {
                'hierarchyLevel': 2,
                'parent': {'duns': ultimate_company['duns']},
            },
        }
        ultimate_company_subsidiary_company_2 = {
            'duns': '222222222',
            'primaryName': faker.company(),
            'corporateLinkage': {
                'hierarchyLevel': 2,
                'parent': {'duns': ultimate_company['duns']},
            },
        }

        tree = create_company_tree(
            [
                ultimate_company,
                ultimate_company_subsidiary_company_1,
                ultimate_company_subsidiary_company_2,
            ],
            ultimate_company_subsidiary_company_1['duns'],
        )

        assert (
            tree['subsidiaries'][0]['duns_number'] == ultimate_company_subsidiary_company_1['duns']
        )

    def test_subsidiary_company_at_end_of_list_is_moved_to_top_when_it_is_the_requested_company(
        self,
        opensearch_with_signals,
    ):
        """When a requested company is a subsidiary company in the tree, check it is moved to the
        top of the list of subsidiaries.
        """
        faker = Faker()

        ultimate_company = {
            'duns': '000000000',
            'primaryName': faker.company(),
            'corporateLinkage': {'hierarchyLevel': 1},
        }
        ultimate_company_subsidiary_company_1 = {
            'duns': '111111111',
            'primaryName': faker.company(),
            'corporateLinkage': {
                'hierarchyLevel': 2,
                'parent': {'duns': ultimate_company['duns']},
            },
        }
        ultimate_company_subsidiary_company_2 = {
            'duns': '222222222',
            'primaryName': faker.company(),
            'corporateLinkage': {
                'hierarchyLevel': 2,
                'parent': {'duns': ultimate_company['duns']},
            },
        }
        ultimate_company_subsidiary_company_3 = {
            'duns': '333333333',
            'primaryName': faker.company(),
            'corporateLinkage': {
                'hierarchyLevel': 2,
                'parent': {'duns': ultimate_company['duns']},
            },
        }
        subsidiary_company_3_subsidiary_company_1 = {
            'duns': '444444444',
            'primaryName': faker.company(),
            'corporateLinkage': {
                'hierarchyLevel': 3,
                'parent': {'duns': ultimate_company_subsidiary_company_3['duns']},
            },
        }

        tree = create_company_tree(
            [
                ultimate_company,
                ultimate_company_subsidiary_company_1,
                ultimate_company_subsidiary_company_2,
                ultimate_company_subsidiary_company_3,
                subsidiary_company_3_subsidiary_company_1,
            ],
            ultimate_company_subsidiary_company_3['duns'],
        )

        assert (
            tree['subsidiaries'][0]['duns_number'] == ultimate_company_subsidiary_company_3['duns']
        )
