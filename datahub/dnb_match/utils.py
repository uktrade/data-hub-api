from enum import Enum


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
