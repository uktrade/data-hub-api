from django.conf import settings
from rest_framework.fields import (
    BooleanField, CharField, ChoiceField, DateField, DecimalField, EmailField, UUIDField,
)


def parse_bool(value):
    """Parses a boolean value from a string."""
    return _parse_value(value, BooleanField())


def parse_date(value):
    """Parses a date from a string."""
    return _parse_value(value, DateField())


def parse_decimal(value, max_digits=19, decimal_places=2):
    """Parses a decimal from a string."""
    return _parse_value(value, DecimalField(max_digits, decimal_places))


def parse_email(value):
    """Parses an email address from a string."""
    return _parse_value(value, EmailField(), blank_value='')


def parse_uuid(value):
    """Parses a UUID from a string."""
    return _parse_value(value, UUIDField())


def parse_uuid_list(value):
    """Parses a comma-separated list of UUIDs from a string."""
    if not value or value.lower().strip() == 'null':
        return []

    field = UUIDField()

    return [field.to_internal_value(item) for item in value.split(',')]


def parse_choice(value, choices, blank_value=''):
    """Parses and validates a value from a list of choices."""
    return _parse_value(value, ChoiceField(choices=choices), blank_value=blank_value)


def parse_limited_string(value, max_length=settings.CHAR_FIELD_MAX_LENGTH):
    """Parses/validates a string."""
    return _parse_value(value, CharField(max_length=max_length), blank_value='')


def _parse_value(value, field, blank_value=None):
    if not value or value.lower().strip() == 'null':
        return blank_value

    field.run_validation(value)
    return field.to_internal_value(value)
