import pytest

from datahub.company.contact_matching import (
    ContactMatchingStatus,
    find_active_contact_by_email_address,
)
from datahub.company.test.factories import ContactFactory


EMAIL_MATCHING_CONTACT_TEST_DATA = [
    {
        'email': 'unique1@primary.com',
        'email_alternative': 'unique1@alternative.com',
        'archived': False,
    },
    {
        'email': 'duplicate@primary.com',
        'email_alternative': '',
        'archived': False,
    },
    {
        'email': 'duplicate@primary.com',
        'email_alternative': '',
        'archived': False,
    },
    {
        'email': 'unique2@primary.com',
        'email_alternative': 'duplicate@alternative.com',
        'archived': False,
    },
    {
        'email': 'unique3@primary.com',
        'email_alternative': 'duplicate@alternative.com',
        'archived': False,
    },
    {
        'email': 'archived1@primary.com',
        'email_alternative': 'archived1@alternative.com',
        'archived': True,
    },
]


@pytest.mark.django_db
@pytest.mark.parametrize(
    'email,expected_matching_status,match_on_alternative',
    (
        # same case, match on email
        ('unique1@primary.com', ContactMatchingStatus.matched, False),
        # same case, match on email_alternative
        ('unique1@alternative.com', ContactMatchingStatus.matched, True),
        # different case, match on email
        ('UNIQUE1@PRIMARY.COM', ContactMatchingStatus.matched, False),
        # different case, match on email_alternative
        ('UNIQUE1@ALTERNATIVE.COM', ContactMatchingStatus.matched, True),
        # different
        ('UNIQUE@COMPANY.IO', ContactMatchingStatus.unmatched, None),
        # duplicate on email
        ('duplicate@primary.com', ContactMatchingStatus.multiple_matches, None),
        # duplicate on email_alternative
        ('duplicate@alternative.com', ContactMatchingStatus.multiple_matches, None),
        # archived contact ignored (email value specified)
        ('archived1@primary.com', ContactMatchingStatus.unmatched, None),
        # archived contact ignored (email_alternative value specified)
        ('archived1@alternative.com', ContactMatchingStatus.unmatched, None),
    ),
)
def test_find_active_contact_by_email_address(
    email,
    expected_matching_status,
    match_on_alternative,
):
    """Test finding a contact by email address for various scenarios."""
    for factory_kwargs in EMAIL_MATCHING_CONTACT_TEST_DATA:
        ContactFactory(**factory_kwargs)

    contact, actual_matching_status = find_active_contact_by_email_address(email)

    assert actual_matching_status == actual_matching_status

    if actual_matching_status == ContactMatchingStatus.matched:
        assert contact
        actual_email = contact.email_alternative if match_on_alternative else contact.email
        assert actual_email.lower() == email.lower()
    else:
        assert not contact
