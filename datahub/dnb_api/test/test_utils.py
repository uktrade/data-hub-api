from urllib.parse import urljoin
from uuid import UUID

import pytest
from django.conf import settings
from rest_framework import serializers, status
from reversion.models import Version

from datahub.company.models import Company
from datahub.company.test.factories import AdviserFactory, CompanyFactory
from datahub.core.serializers import AddressSerializer
from datahub.dnb_api.utils import (
    DNBServiceError,
    DNBServiceInvalidRequest,
    DNBServiceInvalidResponse,
    get_company,
    update_company_from_dnb,
)
from datahub.metadata.models import Country

pytestmark = pytest.mark.django_db


DNB_SEARCH_URL = urljoin(f'{settings.DNB_SERVICE_BASE_URL}/', 'companies/search/')

REQUIRED_REGISTERED_ADDRESS_FIELDS = [
    f'registered_address_{field}' for field in AddressSerializer.REQUIRED_FIELDS
]
# TODO: base these on a DRY list of fields when we add it
ALL_DNB_UPDATED_SERIALIZER_FIELDS = [
    'name',
    'trading_names',
    'address',
    'registered_address',
    'website',
    'number_of_employees',
    'is_number_of_employees_estimated',
    'turnover',
    'is_turnover_estimated',
    'website',
    'global_ultimate_duns_number',
    'company_number',
]
ALL_DNB_UPDATED_FIELDS = [
    'name',
    'trading_names',
    'address_1',
    'address_2',
    'address_county',
    'address_country',
    'address_postcode',
    'registered_address_1',
    'registered_address_2',
    'registered_address_county',
    'registered_address_country',
    'registered_address_postcode',
    'website',
    'number_of_employees',
    'is_number_of_employees_estimated',
    'turnover',
    'is_turnover_estimated',
    'website',
    'global_ultimate_duns_number',
    'company_number',
]


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

    expected_message = f'DNB service returned: {dnb_response_status}'

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

    def _assert_company_synced_with_dnb(self, company, dnb_company, fields=None):  # NOQA: C901
        """
        Check whether the given DataHub company has been synced with the given
        DNB company.
        """
        if not fields:
            fields = ALL_DNB_UPDATED_SERIALIZER_FIELDS

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

        required_registered_address_fields_present = all(
            field in dnb_company for field in REQUIRED_REGISTERED_ADDRESS_FIELDS
        )

        if 'name' in fields:
            assert company.name == dnb_company['primary_name']

        if 'trading_names' in fields:
            assert company.trading_names == dnb_company['trading_names']

        if 'address' in fields:
            assert company.address_1 == dnb_company['address_line_1']
            assert company.address_2 == dnb_company['address_line_2']
            assert company.address_country == country
            assert company.address_town == dnb_company['address_town']
            assert company.address_county == dnb_company['address_county']
            assert company.address_postcode == dnb_company['address_postcode']

        if 'registered_address' in fields and required_registered_address_fields_present:
            assert company.registered_address_1 == dnb_company['registered_address_line_1']
            assert company.registered_address_2 == dnb_company['registered_address_line_2']
            assert company.registered_address_country == registered_country
            assert company.registered_address_town == dnb_company['registered_address_town']
            assert company.registered_address_county == dnb_company['registered_address_county']
            assert (
                company.registered_address_postcode == dnb_company['registered_address_postcode']
            )

        if 'company_number' in fields:
            assert company.company_number == company_number

        if 'number_of_employees' in fields:
            assert company.number_of_employees == dnb_company['employee_number']

        if 'is_number_of_employees_estimated' in fields:
            is_employees_number_estimated = dnb_company['is_employees_number_estimated']
            assert (
                company.is_number_of_employees_estimated == is_employees_number_estimated
            )

        if 'turnover' in fields:
            assert company.turnover == float(dnb_company['annual_sales'])

        if 'is_turnover_estimated' in fields:
            assert company.is_turnover_estimated == dnb_company['is_annual_sales_estimated']

        if 'website' in fields:
            assert company.website == f'http://{dnb_company["domain"]}'

        if 'global_ultimate_duns_number' in fields:
            assert (
                company.global_ultimate_duns_number == dnb_company['global_ultimate_duns_number']
            )

    def _add_address_model_fields(self, fields_set, prefix):
        fields_set.add(f'{prefix}_1')
        fields_set.add(f'{prefix}_2')
        fields_set.add(f'{prefix}_postcode')
        fields_set.add(f'{prefix}_county')
        fields_set.add(f'{prefix}_country')

    @pytest.mark.parametrize(
        'adviser_callable',
        (
            lambda: None,
            lambda: AdviserFactory(),
        ),
    )
    def test_update_company_from_dnb_all_fields(
        self,
        requests_mock,
        dnb_company_search_feature_flag,
        dnb_response_uk,
        adviser_callable,
    ):
        """
        Test that update_company_from_dnb will update all fields when the fields
        kwarg is not specified.
        """
        duns_number = '123456789'
        company = CompanyFactory(duns_number=duns_number, pending_dnb_investigation=True)
        adviser = adviser_callable()
        requests_mock.post(
            DNB_SEARCH_URL,
            json=dnb_response_uk,
        )

        update_company_from_dnb(company, user=adviser)
        company.refresh_from_db()
        dnb_company = dnb_response_uk['results'][0]
        self._assert_company_synced_with_dnb(company, dnb_company)
        assert company.pending_dnb_investigation is False

        versions = list(Version.objects.get_for_object(company))
        assert len(versions) == 1
        version = versions[0]
        assert version.revision.comment == 'Updated from D&B'

        if adviser:
            assert company.modified_by == adviser
            assert version.revision.user == adviser

    @pytest.mark.parametrize(
        'fields_to_update',
        (
            ['global_ultimate_duns_number'],
            ['name', 'address'],
        ),
    )
    def test_update_company_from_dnb_partial_fields(
        self,
        requests_mock,
        dnb_company_search_feature_flag,
        dnb_response_uk,
        fields_to_update,
    ):
        """
        Test that update_company_from_dnb can update a subset of fields.
        """
        duns_number = '123456789'
        company = CompanyFactory(duns_number=duns_number)
        original_company = Company.objects.get(id=company.id)
        requests_mock.post(
            DNB_SEARCH_URL,
            json=dnb_response_uk,
        )

        update_company_from_dnb(company, fields_to_update=fields_to_update)
        company.refresh_from_db()
        dnb_company = dnb_response_uk['results'][0]
        self._assert_company_synced_with_dnb(company, dnb_company, fields=fields_to_update)
        updated_model_fields = set(fields_to_update)

        if 'address' in fields_to_update:
            updated_model_fields.remove('address')
            self._add_address_model_fields(updated_model_fields, 'address')

        if 'registered_address' in fields_to_update:
            updated_model_fields.remove('registered_address')
            self._add_address_model_fields(updated_model_fields, 'registered_address')

        expected_unmodified_fields = set(ALL_DNB_UPDATED_FIELDS) - updated_model_fields
        for field in expected_unmodified_fields:
            original_value = getattr(original_company, field)
            current_value = getattr(company, field)
            assert current_value == original_value

    @pytest.mark.parametrize(
        'dnb_response_code',
        (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ),
    )
    def test_post_dnb_error(self, requests_mock, dnb_response_code):
        """
        Tests that DNBServiceError is raised when calling the DNB API returns a non-200
        status.
        """
        company = CompanyFactory(duns_number='123456789')
        requests_mock.post(
            DNB_SEARCH_URL,
            status_code=dnb_response_code,
        )
        with pytest.raises(DNBServiceError):
            update_company_from_dnb(company)

    @pytest.mark.parametrize(
        'search_results, expected_message',
        (
            (
                ['foo', 'bar'],
                'Something went wrong in an upstream service.',
            ),
            (
                [{'duns_number': '012345678'}],
                'Something went wrong in an upstream service.',
            ),
        ),
    )
    def test_post_dnb_response_invalid(
        self,
        requests_mock,
        search_results,
        expected_message,
    ):
        """
        Tests that DNBServiceInvalidResponse is raised when DNB responds with an unexpected
        response format.
        """
        company = CompanyFactory(duns_number='12345678')
        requests_mock.post(
            DNB_SEARCH_URL,
            json={'results': search_results},
        )
        with pytest.raises(DNBServiceInvalidResponse) as exc:
            update_company_from_dnb(company)
            assert str(exc) == expected_message

    def test_post_dnb_request_invalid(
        self,
        requests_mock,
    ):
        """
        Tests that DNBServiceInvalidRequest is raised when DNB yields no results.
        """
        company = CompanyFactory(duns_number='12345678')
        requests_mock.post(
            DNB_SEARCH_URL,
            json={'results': []},
        )
        with pytest.raises(DNBServiceInvalidRequest) as exc:
            update_company_from_dnb(company)
            assert str(exc) == 'Cannot find a company with duns_number: 12345678'

    def test_post_dnb_data_invalid(
        self,
        requests_mock,
        dnb_response_uk,
    ):
        """
        Tests that ValidationError is raised when data returned by DNB is not valid for saving to a
        Data Hub Company.
        """
        company = CompanyFactory(duns_number='123456789')
        dnb_response_uk['results'][0]['primary_name'] = None
        requests_mock.post(
            DNB_SEARCH_URL,
            json=dnb_response_uk,
        )
        with pytest.raises(serializers.ValidationError) as exc:
            update_company_from_dnb(company)
            assert str(exc) == 'Data from D&B did not pass the Data Hub validation checks.'
