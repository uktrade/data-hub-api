import uuid
from datetime import datetime
from decimal import InvalidOperation
from unittest import mock

import pytest
from django.utils.timezone import utc
from freezegun import freeze_time

from datahub.company.test.factories import CompanyFactory
from datahub.core.constants import Country as CountryConstant
from datahub.core.test_utils import random_obj_for_model
from datahub.dnb_match.constants import DNB_COUNTRY_CODE_MAPPING
from datahub.dnb_match.exceptions import MismatchedRecordsException
from datahub.dnb_match.utils import (
    _extract_address,
    _extract_companies_house_number,
    _extract_country,
    _extract_employees,
    _extract_out_of_business,
    _extract_turnover,
    ARCHIVED_REASON_DISSOLVED,
    EmployeesIndicator,
    extract_wb_record_into_company_fields,
    NATIONAL_ID_SYSTEM_CODE_UK,
    OutOfBusinessIndicator,
    TurnoverIndicator,
    update_company_from_wb_record,
)
from datahub.metadata.models import Country, EmployeeRange, TurnoverRange


FROZEN_TIME = datetime(2019, 1, 1, 1, tzinfo=utc)
UNITED_KINGDOM_COUNTRY_UUID = uuid.UUID(CountryConstant.united_kingdom.value.id)


class TestExtractEmployees:
    """Tests for the _extract_employees function."""

    @pytest.mark.parametrize(
        'wb_record,expected_output',
        (
            # (estimated) Employees Total used
            (
                {
                    'Employees Total': '1',
                    'Employees Total Indicator': EmployeesIndicator.ESTIMATED,
                },
                (1, True),
            ),

            # (estimated because 'modelled') Employees Total used
            (
                {
                    'Employees Total': '1',
                    'Employees Total Indicator': EmployeesIndicator.MODELLED,
                },
                (1, True),
            ),

            # (estimated because 'low end of range') Employees Total used
            (
                {
                    'Employees Total': '1',
                    'Employees Total Indicator': EmployeesIndicator.LOW_END_OF_RANGE,
                },
                (1, True),
            ),

            # (actual) Employees Total used
            (
                {
                    'Employees Total': '111',
                    'Employees Total Indicator': EmployeesIndicator.ACTUAL,
                },
                (111, False),
            ),

            # (estimated) Employees Here used as Employees Total is 0
            (
                {
                    'Employees Total': '0',
                    'Employees Total Indicator': EmployeesIndicator.MODELLED,
                    'Employees Here': '2',
                    'Employees Here Indicator': EmployeesIndicator.ESTIMATED,
                },
                (2, True),
            ),

            # (estimated because 'modelled') Employees Here used as Employees Total is 0
            (
                {
                    'Employees Total': '0',
                    'Employees Total Indicator': EmployeesIndicator.MODELLED,
                    'Employees Here': '2',
                    'Employees Here Indicator': EmployeesIndicator.MODELLED,
                },
                (2, True),
            ),

            # (estimated because 'low end of range') Employees Here used as Employees Total is 0
            (
                {
                    'Employees Total': '0',
                    'Employees Total Indicator': EmployeesIndicator.MODELLED,
                    'Employees Here': '2',
                    'Employees Here Indicator': EmployeesIndicator.LOW_END_OF_RANGE,
                },
                (2, True),
            ),

            # (actual) Employees Here used as Employees Total is 0
            (
                {
                    'Employees Total': '0',
                    'Employees Total Indicator': EmployeesIndicator.MODELLED,
                    'Employees Here': '111',
                    'Employees Here Indicator': EmployeesIndicator.ACTUAL,
                },
                (111, False),
            ),

            # (estimated) Employees Total used as Employees Here is not available
            (
                {
                    'Employees Total': '0',
                    'Employees Total Indicator': EmployeesIndicator.ESTIMATED,
                    'Employees Here': '0',
                    'Employees Here Indicator': EmployeesIndicator.NOT_AVAILABLE,
                },
                (0, True),
            ),

            # Not Available
            (
                {
                    'Employees Total': '0',
                    'Employees Total Indicator': EmployeesIndicator.NOT_AVAILABLE,
                    'Employees Here': '0',
                    'Employees Here Indicator': EmployeesIndicator.NOT_AVAILABLE,
                },
                (None, None),
            ),
        ),
    )
    def test_success(self, wb_record, expected_output):
        """
        Test successful cases related to _extract_employees().
        """
        actual_output = _extract_employees(wb_record)
        assert actual_output == expected_output

    @pytest.mark.parametrize(
        'wb_record,expected_exception',
        (
            # Employees Total is not a number
            (
                {
                    'Employees Total': 'a',
                    'Employees Total Indicator': EmployeesIndicator.ESTIMATED,
                },
                ValueError,
            ),

            # Employees Total is empty
            (
                {
                    'Employees Total': '',
                    'Employees Total Indicator': EmployeesIndicator.ESTIMATED,
                },
                ValueError,
            ),

            # Employees Total Indicator is invalid
            (
                {
                    'Employees Total': '',
                    'Employees Total Indicator': 'a',
                },
                ValueError,
            ),

            # Employees Here is not a number
            (
                {
                    'Employees Total': '0',
                    'Employees Total Indicator': EmployeesIndicator.ESTIMATED,
                    'Employees Here': 'a',
                    'Employees Here Indicator': EmployeesIndicator.ESTIMATED,
                },
                ValueError,
            ),

            # Employees Here is empty
            (
                {
                    'Employees Total': '0',
                    'Employees Total Indicator': EmployeesIndicator.ESTIMATED,
                    'Employees Here': '',
                    'Employees Here Indicator': EmployeesIndicator.ESTIMATED,
                },
                ValueError,
            ),

            # Employees Here Indicator is invalid
            (
                {
                    'Employees Total': '0',
                    'Employees Total Indicator': EmployeesIndicator.ESTIMATED,
                    'Employees Here': '',
                    'Employees Here Indicator': 'a',
                },
                ValueError,
            ),

            # Indicator == NOT_AVAILABLE but Employees value != 0
            (
                {
                    'Employees Total': '1',
                    'Employees Total Indicator': EmployeesIndicator.NOT_AVAILABLE,
                },
                AssertionError,
            ),
        ),
    )
    def test_bad_data(self, wb_record, expected_exception):
        """
        Test cases related to bad input data when calling _extract_employees().
        """
        with pytest.raises(expected_exception):
            _extract_employees(wb_record)


class TestExtractTurnover:
    """Tests for the _extract_turnover function."""

    @pytest.mark.parametrize(
        'wb_record,expected_output',
        (
            # Estimated
            (
                {
                    'Annual Sales in US dollars': '1',
                    'Annual Sales Indicator': TurnoverIndicator.ESTIMATED,
                },
                (1, True),
            ),

            # Modelled
            (
                {
                    'Annual Sales in US dollars': '1',
                    'Annual Sales Indicator': TurnoverIndicator.MODELLED,
                },
                (1, True),
            ),

            # Low end of range
            (
                {
                    'Annual Sales in US dollars': '1',
                    'Annual Sales Indicator': TurnoverIndicator.LOW_END_OF_RANGE,
                },
                (1, True),
            ),

            # Actual
            (
                {
                    'Annual Sales in US dollars': '111',
                    'Annual Sales Indicator': TurnoverIndicator.ACTUAL,
                },
                (111, False),
            ),

            # With scientific notation
            (
                {
                    'Annual Sales in US dollars': '1.03283E+11',
                    'Annual Sales Indicator': TurnoverIndicator.ESTIMATED,
                },
                (103283000000, True),
            ),

            # Float converted to int
            (
                {
                    'Annual Sales in US dollars': '1.5',
                    'Annual Sales Indicator': TurnoverIndicator.ESTIMATED,
                },
                (2, True),
            ),

            # Not available
            (
                {
                    'Annual Sales in US dollars': '0',
                    'Annual Sales Indicator': TurnoverIndicator.NOT_AVAILABLE,
                },
                (None, None),
            ),
        ),
    )
    def test_success(self, wb_record, expected_output):
        """
        Test successful cases related to _extract_turnover().
        """
        actual_output = _extract_turnover(wb_record)
        assert actual_output == expected_output

    @pytest.mark.parametrize(
        'wb_record,exception',
        (
            # Annual Sales in US dollars is not a number
            (
                {
                    'Annual Sales in US dollars': 'a',
                    'Annual Sales Indicator': TurnoverIndicator.ESTIMATED,
                },
                InvalidOperation,
            ),

            # Annual Sales in US dollars is empty
            (
                {
                    'Annual Sales in US dollars': '',
                    'Annual Sales Indicator': TurnoverIndicator.ESTIMATED,
                },
                InvalidOperation,
            ),

            # Annual Sales Indicator is invalid
            (
                {
                    'Annual Sales in US dollars': '1',
                    'Annual Sales Indicator': 'a',
                },
                ValueError,
            ),

            # Indicator == NOT_AVAILABLE but Annual Sales in US dollars value != 0
            (
                {
                    'Annual Sales in US dollars': '1',
                    'Annual Sales Indicator': TurnoverIndicator.NOT_AVAILABLE,
                },
                AssertionError,
            ),
        ),
    )
    def test_bad_data(self, wb_record, exception):
        """
        Test cases related to bad input data when calling _extract_turnover().
        """
        with pytest.raises(exception):
            _extract_turnover(wb_record)


@pytest.mark.django_db
class TestExtractCountry:
    """Tests for the _extract_country function."""

    @pytest.mark.parametrize(
        'wb_country_code,expected_iso_alpha2_code',
        (
            ('790', 'GB'),  # United Kingdom
            ('797', 'GB'),  # Scotland
            ('033', 'AR'),  # Argentina
        ),
    )
    def test_success(self, wb_country_code, expected_iso_alpha2_code):
        """
        Test successful cases related to _extract_country().
        """
        actual_country = _extract_country(wb_country_code)
        assert actual_country.iso_alpha2_code == expected_iso_alpha2_code

    def test_fails_with_non_existent_code(self):
        """
        Test that AssertionError is raised if the given country code
        is not in `constants.DNB_COUNTRY_CODE_MAPPING`.
        """
        with pytest.raises(AssertionError) as excinfo:
            _extract_country('111111')
        assert str(excinfo.value) == (
            'Country code 111111 not recognised, please check DNB_COUNTRY_CODE_MAPPING.'
        )

    def test_fails_with_country_not_mapped(self):
        """
        Test that AssertionError is raised if iso_alpha2_code is None.
        """
        country_code = '898'
        country_mapping = DNB_COUNTRY_CODE_MAPPING[country_code]

        assert not country_mapping['iso_alpha2_code']

        with pytest.raises(AssertionError) as excinfo:
            _extract_country(country_code)
        assert str(excinfo.value) == (
            f'Country {country_mapping["name"]} not currently mapped, '
            'please check DNB_COUNTRY_CODE_MAPPING.'
        )

    @mock.patch.dict(
        'datahub.dnb_match.constants.DNB_COUNTRY_CODE_MAPPING',
        {'897': {'iso_alpha2_code': 'AAA', 'name': 'NOT IN DH'}},
    )
    def test_fails_with_country_not_in_datahub(self):
        """
        Test that Country.DoesNotExist is raised if the country is not in Data Hub.
        """
        with pytest.raises(Country.DoesNotExist) as excinfo:
            _extract_country('897')
        assert str(excinfo.value) == 'Country matching query does not exist.'


@pytest.mark.django_db
class TestExtractAddress:
    """Tests for the _extract_address function."""

    @pytest.mark.parametrize(
        'wb_record,expected_output',
        (
            # all values populated
            (
                {
                    'Street Address': '1',
                    'Street Address 2': 'Main Street',
                    'City Name': 'London',
                    'State/Province Name': 'Camden',
                    'Country Code': '785',
                    'Postal Code for Street Address': 'SW1A 1AA',
                },
                {
                    'address_1': '1',
                    'address_2': 'Main Street',
                    'address_town': 'London',
                    'address_county': 'Camden',
                    'address_country_id': UNITED_KINGDOM_COUNTRY_UUID,
                    'address_postcode': 'SW1A 1AA',
                },
            ),

            # all values blank apart from country
            (
                {
                    'Street Address': '',
                    'Street Address 2': '',
                    'City Name': '',
                    'State/Province Name': '',
                    'Country Code': '785',
                    'Postal Code for Street Address': '',
                },
                {
                    'address_1': '',
                    'address_2': '',
                    'address_town': '',
                    'address_county': '',
                    'address_country_id': UNITED_KINGDOM_COUNTRY_UUID,
                    'address_postcode': '',
                },
            ),
        ),
    )
    def test_success(self, wb_record, expected_output):
        """
        Test successful cases related to _extract_address().
        """
        actual_output = _extract_address(wb_record)
        assert actual_output == expected_output


class TestExtractCompaniesHouseNumber:
    """Tests for the _extract_companies_house_number function."""

    @pytest.mark.parametrize(
        'wb_record,expected_output',
        (
            # System Code == UK CH
            (
                {
                    'National Identification Number': '12345678',
                    'National Identification System Code': str(NATIONAL_ID_SYSTEM_CODE_UK),
                },
                '12345678',
            ),

            # System Code == UK CH and CHN == ''
            (
                {
                    'National Identification Number': '',
                    'National Identification System Code': str(NATIONAL_ID_SYSTEM_CODE_UK),
                },
                '',
            ),

            # System Code == UK CH and len(CHN) != 8
            (
                {
                    'National Identification Number': '1',
                    'National Identification System Code': str(NATIONAL_ID_SYSTEM_CODE_UK),
                },
                '00000001',
            ),

            # System Code == UK CH and len(CHN) > 8 (shouldn't happen but still testing the case)
            (
                {
                    'National Identification Number': '123456789',
                    'National Identification System Code': str(NATIONAL_ID_SYSTEM_CODE_UK),
                },
                '123456789',
            ),

            # System Code != UK CH
            (
                {
                    'National Identification Number': '123456789',
                    'National Identification System Code': '0',
                },
                '',
            ),

            # System Code == ''
            (
                {
                    'National Identification Number': '123456789',
                    'National Identification System Code': '',
                },
                '',
            ),
        ),
    )
    def test_success(self, wb_record, expected_output):
        """
        Test successful cases related to _extract_companies_house_number().
        """
        actual_output = _extract_companies_house_number(wb_record)
        assert actual_output == expected_output

    @pytest.mark.parametrize(
        'wb_record',
        (
            {
                'National Identification Number': '123456789',
                'National Identification System Code': 'a',
            },
        ),
    )
    def test_bad_data(self, wb_record):
        """
        Test cases related to bad input data when calling _extract_companies_house_number().
        """
        with pytest.raises(ValueError):
            _extract_companies_house_number(wb_record)


class TestExtractOutOfBusiness:
    """Tests for the _extract_out_of_business function."""

    @pytest.mark.parametrize(
        'wb_record,expected_output',
        (
            (
                {
                    'Out of Business indicator': OutOfBusinessIndicator.OUT_OF_BUSINESS,
                },
                True,
            ),

            (
                {
                    'Out of Business indicator': OutOfBusinessIndicator.NOT_OUT_OF_BUSINESS,
                },
                False,
            ),
        ),
    )
    def test_success(self, wb_record, expected_output):
        """
        Test successful cases related to _extract_out_of_business().
        """
        actual_output = _extract_out_of_business(wb_record)
        assert actual_output == expected_output

    @pytest.mark.parametrize(
        'wb_record',
        (
            {
                'Out of Business indicator': 'M',
            },

            {
                'Out of Business indicator': '',
            },

            {
                'Out of Business indicator': 1,
            },
        ),
    )
    def test_bad_data(self, wb_record):
        """
        Test cases related to bad input data when calling _extract_out_of_business().
        """
        with pytest.raises(ValueError):
            _extract_out_of_business(wb_record)


@pytest.mark.django_db
class TestExtractWbRecordIntoCompanyFields:
    """Tests for the extract_wb_record_into_company_fields function."""

    @pytest.mark.parametrize(
        'wb_record,expected_output',
        (
            # Complete record
            (
                {
                    'DUNS Number': '112233445566',
                    'Business Name': 'WB Corp',
                    'Secondary Name': 'Known as...',
                    'Employees Total': '11',
                    'Employees Total Indicator': EmployeesIndicator.ESTIMATED,
                    'Employees Here': '0',
                    'Employees Here Indicator': EmployeesIndicator.ESTIMATED,
                    'Annual Sales in US dollars': '100',
                    'Annual Sales Indicator': TurnoverIndicator.ESTIMATED,
                    'Street Address': '1',
                    'Street Address 2': 'Main Street',
                    'City Name': 'London',
                    'State/Province Name': 'Camden',
                    'Country Code': '785',
                    'Postal Code for Street Address': 'SW1A 1AA',
                    'National Identification Number': '12345678',
                    'National Identification System Code': str(NATIONAL_ID_SYSTEM_CODE_UK),
                    'Out of Business indicator': OutOfBusinessIndicator.NOT_OUT_OF_BUSINESS,
                },
                (
                    {
                        'duns_number': '112233445566',
                        'name': 'WB Corp',
                        'trading_names': ['Known as...'],
                        'company_number': '12345678',
                        'number_of_employees': 11,
                        'is_number_of_employees_estimated': True,
                        'employee_range': None,
                        'turnover': 100,
                        'is_turnover_estimated': True,
                        'turnover_range': None,
                        'address_1': '1',
                        'address_2': 'Main Street',
                        'address_town': 'London',
                        'address_county': 'Camden',
                        'address_country_id': UNITED_KINGDOM_COUNTRY_UUID,
                        'address_postcode': 'SW1A 1AA',
                        'registered_address_1': '1',
                        'registered_address_2': 'Main Street',
                        'registered_address_town': 'London',
                        'registered_address_county': 'Camden',
                        'registered_address_country_id': UNITED_KINGDOM_COUNTRY_UUID,
                        'registered_address_postcode': 'SW1A 1AA',
                        'trading_address_1': '1',
                        'trading_address_2': 'Main Street',
                        'trading_address_town': 'London',
                        'trading_address_county': 'Camden',
                        'trading_address_country_id': UNITED_KINGDOM_COUNTRY_UUID,
                        'trading_address_postcode': 'SW1A 1AA',
                    },
                    False,
                ),
            ),

            # Minimal record
            (
                {
                    'DUNS Number': '112233445566',
                    'Business Name': 'WB Corp',
                    'Secondary Name': '',
                    'Employees Total': '0',
                    'Employees Total Indicator': EmployeesIndicator.NOT_AVAILABLE,
                    'Employees Here': '0',
                    'Employees Here Indicator': EmployeesIndicator.NOT_AVAILABLE,
                    'Annual Sales in US dollars': '0',
                    'Annual Sales Indicator': TurnoverIndicator.NOT_AVAILABLE,
                    'Street Address': '',
                    'Street Address 2': '',
                    'City Name': '',
                    'State/Province Name': '',
                    'Country Code': '785',
                    'Postal Code for Street Address': '',
                    'National Identification Number': '',
                    'National Identification System Code': '',
                    'Out of Business indicator': OutOfBusinessIndicator.OUT_OF_BUSINESS,
                },
                (
                    {
                        'duns_number': '112233445566',
                        'name': 'WB Corp',
                        'trading_names': [],
                        'company_number': '',
                        'number_of_employees': None,
                        'is_number_of_employees_estimated': None,
                        'employee_range': None,
                        'turnover': None,
                        'is_turnover_estimated': None,
                        'turnover_range': None,
                        'address_1': '',
                        'address_2': '',
                        'address_town': '',
                        'address_county': '',
                        'address_country_id': UNITED_KINGDOM_COUNTRY_UUID,
                        'address_postcode': '',
                        'registered_address_1': '',
                        'registered_address_2': '',
                        'registered_address_town': '',
                        'registered_address_county': '',
                        'registered_address_country_id': UNITED_KINGDOM_COUNTRY_UUID,
                        'registered_address_postcode': '',
                        'trading_address_1': '',
                        'trading_address_2': '',
                        'trading_address_town': '',
                        'trading_address_county': '',
                        'trading_address_country_id': UNITED_KINGDOM_COUNTRY_UUID,
                        'trading_address_postcode': '',
                    },
                    True,
                ),
            ),
        ),
    )
    def test_success(self, wb_record, expected_output):
        """
        Test successful cases related to extract_wb_record_into_company_fields().
        """
        actual_output = extract_wb_record_into_company_fields(wb_record)
        assert actual_output == expected_output


@pytest.mark.django_db
class TestUpdateCompanyFromWbRecord:
    """Tests related to the function update_company_from_wb_record."""

    @pytest.mark.parametrize(
        'wb_record,expected_fields',
        (
            # Complete record
            (
                {
                    'DUNS Number': '123456789',
                    'Business Name': 'WB Corp',
                    'Secondary Name': 'Known as...',
                    'Employees Total': '11',
                    'Employees Total Indicator': EmployeesIndicator.ESTIMATED,
                    'Employees Here': '0',
                    'Employees Here Indicator': EmployeesIndicator.ESTIMATED,
                    'Annual Sales in US dollars': '100',
                    'Annual Sales Indicator': TurnoverIndicator.ESTIMATED,
                    'Street Address': '1',
                    'Street Address 2': 'Main Street',
                    'City Name': 'London',
                    'State/Province Name': 'Camden',
                    'Country Code': '785',
                    'Postal Code for Street Address': 'SW1A 1AA',
                    'National Identification Number': '12345678',
                    'National Identification System Code': str(NATIONAL_ID_SYSTEM_CODE_UK),
                    'Out of Business indicator': OutOfBusinessIndicator.NOT_OUT_OF_BUSINESS,
                },
                {
                    'duns_number': '123456789',
                    'name': 'WB Corp',
                    'trading_names': ['Known as...'],
                    'company_number': '12345678',
                    'number_of_employees': 11,
                    'is_number_of_employees_estimated': True,
                    'employee_range': None,
                    'turnover': 100,
                    'is_turnover_estimated': True,
                    'turnover_range': None,
                    'address_1': '1',
                    'address_2': 'Main Street',
                    'address_town': 'London',
                    'address_county': 'Camden',
                    'address_country_id': UNITED_KINGDOM_COUNTRY_UUID,
                    'address_postcode': 'SW1A 1AA',
                    'registered_address_1': '1',
                    'registered_address_2': 'Main Street',
                    'registered_address_town': 'London',
                    'registered_address_county': 'Camden',
                    'registered_address_country_id': UNITED_KINGDOM_COUNTRY_UUID,
                    'registered_address_postcode': 'SW1A 1AA',
                    'trading_address_1': '1',
                    'trading_address_2': 'Main Street',
                    'trading_address_town': 'London',
                    'trading_address_county': 'Camden',
                    'trading_address_country_id': UNITED_KINGDOM_COUNTRY_UUID,
                    'trading_address_postcode': 'SW1A 1AA',
                },
            ),

            # Minimal record / archives the Data Hub Company as well
            (
                {
                    'DUNS Number': '123456789',
                    'Business Name': 'WB Corp',
                    'Secondary Name': '',
                    'Employees Total': '0',
                    'Employees Total Indicator': EmployeesIndicator.NOT_AVAILABLE,
                    'Employees Here': '0',
                    'Employees Here Indicator': EmployeesIndicator.NOT_AVAILABLE,
                    'Annual Sales in US dollars': '0',
                    'Annual Sales Indicator': TurnoverIndicator.NOT_AVAILABLE,
                    'Street Address': '',
                    'Street Address 2': '',
                    'City Name': '',
                    'State/Province Name': '',
                    'Country Code': '785',
                    'Postal Code for Street Address': '',
                    'National Identification Number': '',
                    'National Identification System Code': '',
                    'Out of Business indicator': OutOfBusinessIndicator.OUT_OF_BUSINESS,
                },
                {
                    'duns_number': '123456789',
                    'name': 'WB Corp',
                    'trading_names': [],
                    'company_number': '',
                    'number_of_employees': None,
                    'is_number_of_employees_estimated': None,
                    'employee_range': None,
                    'turnover': None,
                    'is_turnover_estimated': None,
                    'turnover_range': None,
                    'address_1': '',
                    'address_2': '',
                    'address_town': '',
                    'address_county': '',
                    'address_country_id': UNITED_KINGDOM_COUNTRY_UUID,
                    'address_postcode': '',
                    'registered_address_1': '',
                    'registered_address_2': '',
                    'registered_address_town': '',
                    'registered_address_county': '',
                    'registered_address_country_id': UNITED_KINGDOM_COUNTRY_UUID,
                    'registered_address_postcode': '',
                    'trading_address_1': '',
                    'trading_address_2': '',
                    'trading_address_town': '',
                    'trading_address_county': '',
                    'trading_address_country_id': UNITED_KINGDOM_COUNTRY_UUID,
                    'trading_address_postcode': '',
                    'archived': True,
                    'archived_on': FROZEN_TIME,
                    'archived_reason': ARCHIVED_REASON_DISSOLVED,
                },
            ),
        ),
    )
    @freeze_time(FROZEN_TIME)
    def test_update(self, wb_record, expected_fields):
        """
        Test that update_company_from_wb_record updates the company with the data from wb_record.
        """
        company = CompanyFactory(
            duns_number=None,
            name='Previous name',
            trading_names=['Previous trading name'],
            company_number='87654321',
            number_of_employees=999,
            is_number_of_employees_estimated=False,
            employee_range=random_obj_for_model(EmployeeRange),
            turnover=888,
            is_turnover_estimated=False,
            turnover_range=random_obj_for_model(TurnoverRange),
            address_1='999',
            address_2='Street Main',
            address_town='Manchester',
            address_county='Manchester',
            address_country_id=UNITED_KINGDOM_COUNTRY_UUID,
            address_postcode='M90 1QX',
            registered_address_1='999',
            registered_address_2='Street Main',
            registered_address_town='Manchester',
            registered_address_county='Manchester',
            registered_address_country_id=UNITED_KINGDOM_COUNTRY_UUID,
            registered_address_postcode='M90 1QX',
            trading_address_1='999',
            trading_address_2='Street Main',
            trading_address_town='Manchester',
            trading_address_county='Manchester',
            trading_address_country_id=UNITED_KINGDOM_COUNTRY_UUID,
            trading_address_postcode='M90 1QX',
            archived=False,
            archived_on=None,
            archived_reason='',
        )
        updated_fields = update_company_from_wb_record(company, wb_record)

        actual_fields = {
            field_name: getattr(company, field_name)
            for field_name in expected_fields
        }
        assert actual_fields == expected_fields
        assert set(updated_fields) == set(expected_fields)

    def test_fails_if_entities_have_different_duns_numbers(self):
        """
        Test that if the DUNS number of the company is different from the
        one specified in the Worldbase record, a MismatchedRecordsException
        is raised.
        """
        company = CompanyFactory.build(duns_number='987654321')
        wb_record = {
            'DUNS Number': '123456789',
            'Business Name': 'WB Corp',
            'Secondary Name': '',
            'Employees Total': '0',
            'Employees Total Indicator': EmployeesIndicator.NOT_AVAILABLE,
            'Employees Here': '0',
            'Employees Here Indicator': EmployeesIndicator.NOT_AVAILABLE,
            'Annual Sales in US dollars': '0',
            'Annual Sales Indicator': TurnoverIndicator.NOT_AVAILABLE,
            'Street Address': '',
            'Street Address 2': '',
            'City Name': '',
            'State/Province Name': '',
            'Country Code': '785',
            'Postal Code for Street Address': '',
            'National Identification Number': '',
            'National Identification System Code': '',
            'Out of Business indicator': OutOfBusinessIndicator.OUT_OF_BUSINESS,
        }

        with pytest.raises(MismatchedRecordsException) as excinfo:
            update_company_from_wb_record(company, wb_record)

        assert str(excinfo.value) == (
            'The Worldbase record with DUNS number 123456789 cannot be used to '
            f'update company {company.id} with DUNS number 987654321.'
        )
