from enum import Enum, IntEnum
from typing import Optional, Tuple

from django.db.models import Count

from datahub.company.models import Contact
from datahub.core.query_utils import get_queryset_object

# NOTE: We may want to review our approach with this utility mechanism if we
# need to add further strategies.  It could be that a better approach is to move
# logic to the model layer - as part of a Manager class - and also use exceptions
# to better signpost matching problems as opposed to returning a value and status


def _match_contact(filter_criteria):
    """
    This default matching strategy function will attempt to get a single result
    for the specified criteria.
    It will fail with an `unmatched` result if there are no matching contacts.
    It will fail with a `multiple_matches` result if there are multiple matches
    for this criteria.
    """
    contact = None
    try:
        contact = get_queryset_object(Contact.objects.all(), **filter_criteria)
        contact_matching_status = ContactMatchingStatus.matched
    except Contact.DoesNotExist:
        contact_matching_status = ContactMatchingStatus.unmatched
    except Contact.MultipleObjectsReturned:
        contact_matching_status = ContactMatchingStatus.multiple_matches

    return contact, contact_matching_status


def _match_contact_max_interactions(filter_criteria):
    """
    This matching strategy function is the same as the default strategy, except
    that it will prefer to return the contact with the most interactions in the
    case where there are multiple contacts that match the criteria.
    """
    contact = None
    try:
        contact = Contact.objects.filter(
            **filter_criteria,
        ).annotate(
            interactions_count=Count('interactions'),
        ).order_by(
            '-interactions_count',
            'pk',
        )[0]
        contact_matching_status = ContactMatchingStatus.matched
    except IndexError:
        contact_matching_status = ContactMatchingStatus.unmatched

    return contact, contact_matching_status


def _find_active_contact_using_field(value, lookup_field, match_strategy_func):
    """
    Looks up a contact by performing a case-insensitive search on a particular field.

    Only non-archived contacts are considered.

    :param value: The value to search for
    :param lookup_field: The name of the field to search
    :param match_strategy_func: The function to use when matching a contact
    """
    filter_kwargs = {
        'archived': False,
        f'{lookup_field}__iexact': value,
    }
    return match_strategy_func(filter_kwargs)


class MatchStrategy(Enum):
    """
    Enum of contact match strategy functions.
    """

    MAX_INTERACTIONS = _match_contact_max_interactions
    DEFAULT = _match_contact


class ContactMatchingStatus(IntEnum):
    """Matching status (for when searching for a contact by email address)."""

    matched = 1
    unmatched = 2
    multiple_matches = 3


def find_active_contact_by_email_address(
    email,
    match_strategy_func=MatchStrategy.DEFAULT,
) -> Tuple[Optional[Contact], ContactMatchingStatus]:
    """
    Attempts to find a contact by email address.  Returns a tuple consisting of
    the Contact that was found (or None) and the ContactMatchingStatus.

    Used e.g. when importing interactions to match interactions to contacts using an
    email address.

    Only non-archived contacts are checked.

    The following the logic is used:
    - if a unique match is found using Contact.email, this is used
    - otherwise, if there is a unique match on Contact.email_alternative, this is used
    - matching using one of these fields is delegated to the specified `match_strategy` -
      or a default strategy if this is unspecified.
      The match strategy will determine whether a contact is found according to
      certain situations - the ContactMatchingStatus returned will be set by
      the match strategy.
    """
    contact, matching_status = _find_active_contact_using_field(
        email,
        'email',
        match_strategy_func,
    )
    if matching_status == ContactMatchingStatus.unmatched:
        contact, matching_status = _find_active_contact_using_field(
            email,
            'email_alternative',
            match_strategy_func,
        )

    return contact, matching_status
