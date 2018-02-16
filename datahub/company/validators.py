import re
from datahub.core.constants import HeadquarterType

_INVALID_COMPANY_NUMBER_RE = re.compile(r'[^A-Z0-9]')


def has_uk_establishment_number_prefix(value):
    """Checks if a UK establishment number has the correct (BR) prefix."""
    return not value or value.startswith('BR')


def has_no_invalid_company_number_characters(value):
    """Checks if a UK establishment number only has valid characters."""
    return not value or not _INVALID_COMPANY_NUMBER_RE.search(value)


def is_company_a_global_headquarters(value):
    """Checks if company is a global headquarters."""
    if value is None or value.headquarter_type is None:
        return False

    return str(value.headquarter_type.id) == HeadquarterType.ghq.value.id
