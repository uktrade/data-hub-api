from enum import IntEnum
from typing import Optional, Tuple

from datahub.company.models import Contact


class ContactMatchingStatus(IntEnum):
    """Matching status (for when searching for a contact by email address)."""

    matched = 1
    unmatched = 2
    multiple_matches = 3


def find_active_contact_by_email_address(email) -> Tuple[Optional[Contact], ContactMatchingStatus]:
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
    if matching_status == ContactMatchingStatus.unmatched:
        contact, matching_status = _find_active_contact_using_field(email, 'email_alternative')

    return contact, matching_status


def _find_active_contact_using_field(value, lookup_field):
    """
    Looks up a contact by performing a case-insensitive search on a particular field.

    Only non-archived contacts are considered.

    :param value: The value to search for
    :param lookup_field: The name of the field to search
    """
    contact = None
    get_kwargs = {
        'archived': False,
        f'{lookup_field}__iexact': value,
    }

    try:
        contact = Contact.objects.get(**get_kwargs)
        contact_matching_status = ContactMatchingStatus.matched
    except Contact.DoesNotExist:
        contact_matching_status = ContactMatchingStatus.unmatched
    except Contact.MultipleObjectsReturned:
        contact_matching_status = ContactMatchingStatus.multiple_matches

    return contact, contact_matching_status
