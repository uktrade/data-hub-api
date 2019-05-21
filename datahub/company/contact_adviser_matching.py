from enum import IntEnum
from typing import Optional, Tuple

from datahub.company.models import Advisor, Contact


class MatchingStatus(IntEnum):
    """Matching status (for when searching for a model instance by a lookup field)."""

    matched = 1
    unmatched = 2
    multiple_matches = 3


def find_active_contact_by_email_address(email) -> Tuple[Optional[Contact], MatchingStatus]:
    """
    Attempts to find a contact by email address.

    Used e.g. when importing interactions to match interactions to contacts using an
    email address.

    Only non-archived contacts are checked.

    The following the logic is used:
    - if a unique match is found using Contact.email, this is used
    - if there are multiple matches found using Contact.email, matching aborts
    - otherwise, if there is a unique match on Contact.email_alternative, this is used
    """
    contact, matching_status = _find_active_contact_using_field(email, 'email')
    if matching_status == MatchingStatus.unmatched:
        contact, matching_status = _find_active_contact_using_field(email, 'email_alternative')

    return contact, matching_status


def find_active_adviser_by_email_address(email) -> Tuple[Optional[Contact], MatchingStatus]:
    """
    Attempts to find an adviser by email address.

    Used e.g. when importing interactions to match interactions to Advisors using an
    email address.

    Only active Advisors are checked.

    The following the logic is used:
    - if a unique match is found using Advisor.email, this is used
    - if there are multiple matches found using Advisor.contact_email, matching aborts
    - otherwise, if there is a unique match on Contact.contact_email, this is used
    """
    adviser, matching_status = _find_active_adviser_using_field(email, 'email')
    if matching_status == MatchingStatus.unmatched:
        adviser, matching_status = _find_active_adviser_using_field(email, 'contact_email')

    return adviser, matching_status


def _find_active_contact_using_field(value, lookup_field):
    return _find_model_instance_using_field(
        Contact,
        value,
        lookup_field,
        extra_filters={'archived': False},
    )


def _find_active_adviser_using_field(value, lookup_field):
    return _find_model_instance_using_field(
        Advisor,
        value,
        lookup_field,
        extra_filters={'is_active': True},
    )


def _find_model_instance_using_field(model_class, value, lookup_field, extra_filters=None):
    """
    Looks up a model instance by performing a case-insensitive search on a particular field.

    :param model_class: The model class to use for the lookup
    :param value: The value to search for
    :param lookup_field: The name of the field to search
    :param extra_filters: Optional - any additional field filters to filter results with
    """
    if not extra_filters:
        extra_filters = {}
    result = None
    get_kwargs = {
        f'{lookup_field}__iexact': value,
        **extra_filters,
    }

    try:
        result = model_class.objects.get(**get_kwargs)
        matching_status = MatchingStatus.matched
    except model_class.DoesNotExist:
        matching_status = MatchingStatus.unmatched
    except model_class.MultipleObjectsReturned:
        matching_status = MatchingStatus.multiple_matches

    return result, matching_status
