from datetime import date

from dateutil.relativedelta import relativedelta


def field_incomplete(combiner, field):
    """Checks whether a field has been filled in."""
    if combiner.is_field_to_many(field):
        return not combiner.get_value_to_many(field)
    return combiner.get_value(field) in (None, '')


def _is_provided_and_is_date_in_the_past(value):
    """
    Returns True if the date value is provided and is today's date or in the past.

    Note that comparing the date to today's date could cause issues
    with users who are in different timezones as they could be in front of UTC.

    TODO: Consider a users timezone when comparing the date values.
    """
    if not value:
        return False
    return date.today() >= value


def is_provided_and_is_date_less_than_a_year_ago(value):
    """Returns True if the date value is provided and within the last year."""
    if not value:
        return False
    return _is_provided_and_is_date_in_the_past(
        value,
    ) and (
        value > date.today() - relativedelta(years=1)
    )
