from rest_framework.fields import BooleanField, DateField, EmailField, UUIDField


def parse_bool(value):
    """Parses a boolean value from a string."""
    return _parse_value(value, BooleanField())


def parse_date(value):
    """Parses a date from a string."""
    return _parse_value(value, DateField())


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


def _parse_value(value, field, blank_value=None):
    if not value or value.lower().strip() == 'null':
        return blank_value

    field.run_validation(value)
    return field.to_internal_value(value)
