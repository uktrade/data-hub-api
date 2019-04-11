from decimal import Decimal
from enum import Enum
from functools import lru_cache

from django.utils.timezone import now

from datahub.dnb_match.constants import DNB_COUNTRY_CODE_MAPPING
from datahub.dnb_match.exceptions import MismatchedRecordsException
from datahub.metadata.models import Country


ARCHIVED_REASON_DISSOLVED = 'Company is dissolved'
NATIONAL_ID_SYSTEM_CODE_UK = 12


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


class OutOfBusinessIndicator(Enum):
    """Indicates if a business is out of business."""

    OUT_OF_BUSINESS = 'Y'
    NOT_OUT_OF_BUSINESS = 'N'


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
        'address_country_id': country.id,
        'address_postcode': wb_record['Postal Code for Street Address'],
    }


def _extract_companies_house_number(wb_record):
    """
    :returns: the companies house number for the given D&B Worldbase
        record or an empty string
    """
    system_code = wb_record['National Identification System Code']
    if not system_code or int(system_code) != NATIONAL_ID_SYSTEM_CODE_UK:
        return ''

    companies_house_number = wb_record['National Identification Number']
    if companies_house_number:
        # companies house numbers are length 8
        return companies_house_number.zfill(8)

    return ''


def _extract_out_of_business(wb_record):
    """
    :returns: Yes if the given D&B worldbase indicates that the record is out
        of business
    """
    raw_value = wb_record['Out of Business indicator']
    return OutOfBusinessIndicator(raw_value) == OutOfBusinessIndicator.OUT_OF_BUSINESS


def extract_wb_record_into_company_fields(wb_record):
    """
    :returns (fields, is_out_of_business) where:
        fields: dict of company field names and new values
        is_out_of_business: True if the record is out of business
    """
    duns_number = wb_record['DUNS Number']
    name = wb_record['Business Name']
    trading_name = wb_record['Secondary Name']
    number_of_employees, is_number_of_employees_estimated = _extract_employees(wb_record)
    turnover, is_turnover_estimated = _extract_turnover(wb_record)
    companies_house_number = _extract_companies_house_number(wb_record)
    is_out_of_business = _extract_out_of_business(wb_record)
    address = _extract_address(wb_record)

    company_fields = {
        'name': name,
        'trading_names': [trading_name] if trading_name else [],
        'company_number': companies_house_number,
        'duns_number': duns_number,
        'number_of_employees': number_of_employees,
        'is_number_of_employees_estimated': is_number_of_employees_estimated,
        'employee_range': None,  # resetting it as deprecated
        'turnover': turnover,
        'is_turnover_estimated': is_turnover_estimated,
        'turnover_range': None,  # resetting it as deprecated
    }

    # TODO: registered_address is been currently set as the frontend has not moved to
    # the new address logic yet. If that happens before this logic is run or re-run,
    # it would be more accurate to set registered_address fields to None or
    # process the Worldbase field 'Registered Address Indicator'.
    # This is because the given D&B address is the principal address which is
    # different from the registered one unless 'Registered Address Indicator' = 'Y'
    company_fields.update(
        **address,
        **{
            f'trading_{address_field}': address_value
            for address_field, address_value in address.items()
        },
        **{
            f'registered_{address_field}': address_value
            for address_field, address_value in address.items()
        },
    )

    return company_fields, is_out_of_business


def update_company_from_wb_record(company, wb_record, commit=True):
    """
    Updates company with data from the Worldbase record wb_record.
    :param commit: if False, the changes will not be saved
    :raises MismatchedRecordsException: if the Worldbase record and the Data Hub
        company have different DUNS numbers.
    :returns: list of updated fields
    """
    company_fields, is_out_of_business = extract_wb_record_into_company_fields(wb_record)

    if company.duns_number and company.duns_number != company_fields['duns_number']:
        raise MismatchedRecordsException(
            f'The Worldbase record with DUNS number {company_fields["duns_number"]} cannot '
            f'be used to update company {company.id} with DUNS number {company.duns_number}.',
        )

    # update company fields
    for field_name, field_value in company_fields.items():
        setattr(company, field_name, field_value)
    updated_fields = list(company_fields)

    # archive if necessary
    if is_out_of_business and not company.archived:
        company.archived = True
        company.archived_reason = ARCHIVED_REASON_DISSOLVED
        company.archived_on = now()

        updated_fields += [
            'archived',
            'archived_reason',
            'archived_on',
        ]

    if commit:
        company.save(update_fields=updated_fields)
    return updated_fields
