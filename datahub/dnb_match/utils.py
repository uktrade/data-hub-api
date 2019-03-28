from decimal import Decimal
from enum import Enum
from functools import lru_cache

from datahub.dnb_match.constants import DNB_COUNTRY_CODE_MAPPING
from datahub.metadata.models import Country



class EmployeesIndicator(Enum):
    """
    Indicates if the field Employees Total/Here is an actual value,
    estimated value or not available.
    """

    NOT_AVAILABLE = ''
    ACTUAL = '0'
    LOW_END_OF_RANGE = '1'
    ESTIMATED = '2'
    MODELLED = '3'


class TurnoverIndicator(Enum):
    """
    Indicates if the field 'Annual Sales in US dollars' is an actual value,
    estimated value or not available.
    """

    NOT_AVAILABLE = ''
    ACTUAL = '0'
    LOW_END_OF_RANGE = '1'
    ESTIMATED = '2'
    MODELLED = '3'


def _extract_employees(wb_record):
    """
    Returns a tuple with number of employees as an int and a bool indicating
    if that value is estimated or not.
    The data is extracted from the 'Employees Total' field in the Worldbase record
    if defined or 'Employees Here' otherwise.
    None values are returned if the data is not available in the Worldbase record.

    :returns: (number_of_employees, is_number_of_employees_estimated) for the
        given D&B Worldbase record or (None, None) if the data is not available in the record
    """
    number_of_employees = int(wb_record['Employees Total'])
    employees_indicator = EmployeesIndicator(wb_record['Employees Total Indicator'])

    if not number_of_employees:
        employees_here_indicator = EmployeesIndicator(wb_record['Employees Here Indicator'])
        if employees_here_indicator != EmployeesIndicator.NOT_AVAILABLE:
            number_of_employees = int(wb_record['Employees Here'])
            employees_indicator = employees_here_indicator

    if employees_indicator == EmployeesIndicator.NOT_AVAILABLE:
        assert not number_of_employees

        return None, None

    is_number_of_employees_estimated = employees_indicator != EmployeesIndicator.ACTUAL

    return number_of_employees, is_number_of_employees_estimated


def _extract_turnover(wb_record):
    """
    Returns a tuple with the turnover as an int and a bool indicating if the value
    is estimated or not.
    None values are returned if the data is not available in the Worldbase record.

    :returns: (turnover, is_turnover_estimated) for the given D&B Worldbase record
        or (None, None) if the data is not available in the record
    """
    turnover = round(Decimal(wb_record['Annual Sales in US dollars']))
    turnover_indicator = TurnoverIndicator(wb_record['Annual Sales Indicator'])

    if turnover_indicator == turnover_indicator.NOT_AVAILABLE:
        assert not turnover

        return None, None

    is_turnover_estimated = turnover_indicator != turnover_indicator.ACTUAL

    return turnover, is_turnover_estimated


@lru_cache()
def _extract_country(wb_country_code):
    """
    :returns: instance of Country for given DnB country code
    :raises: AssertionError in case of unexpected non-implemented scenarios
    :raises: Country.DoesNotExist if the DnB Country could not be
        found in the Data Hub
    """
    assert wb_country_code in DNB_COUNTRY_CODE_MAPPING, (
        f'Country code {wb_country_code} not recognised, please check DNB_COUNTRY_CODE_MAPPING.'
    )

    dnb_country_data = DNB_COUNTRY_CODE_MAPPING[wb_country_code]
    assert dnb_country_data['iso_alpha2_code'], (
        f'Country {dnb_country_data["name"]} not currently mapped, '
        'please check DNB_COUNTRY_CODE_MAPPING.'
    )

    return Country.objects.get(
        iso_alpha2_code=dnb_country_data['iso_alpha2_code'],
    )


def _extract_address(wb_record):
    """
    :returns: dict with address for the given D&B Worldbase record
    :raises: AssertionError in case of unexpected non-implemented scenarios
    :raises: Country.DoesNotExist if the DnB Country could not be
        found in Data Hub
    """
    country = _extract_country(wb_record['Country Code'])
    return {
        'address_1': wb_record['Street Address'],
        'address_2': wb_record['Street Address 2'],
        'address_town': wb_record['City Name'],
        'address_county': wb_record['State/Province Name'],
        'address_country': country,
        'address_postcode': wb_record['Postal Code for Street Address'],
    }
