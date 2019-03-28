from decimal import InvalidOperation
from unittest import mock

import pytest

from datahub.dnb_match.constants import DNB_COUNTRY_CODE_MAPPING
from datahub.dnb_match.utils import (
    _extract_country,
    _extract_employees,
    _extract_turnover,
    EmployeesIndicator,
    TurnoverIndicator,
)
from datahub.metadata.models import Country


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
