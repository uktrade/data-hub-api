import pytest

from datahub.company.contact_adviser_matching import (
    find_active_adviser_by_email_address,
    find_active_contact_by_email_address,
    MatchingStatus,
)
from datahub.company.test.factories import AdviserFactory, ContactFactory


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


EMAIL_MATCHING_ADVISER_TEST_DATA = [
    {
        'email': 'unique1@primary.com',
        'contact_email': 'unique1@alternative.com',
        'is_active': True,
    },
    {
        'email': 'duplicate@primary.com',
        'contact_email': '',
        'is_active': True,
    },
    {
        'email': 'unique2@primary.com',
        'contact_email': 'duplicate@alternative.com',
        'is_active': True,
    },
    {
        'email': 'unique3@primary.com',
        'contact_email': 'duplicate@alternative.com',
        'is_active': True,
    },
    {
        'email': 'archived1@primary.com',
        'contact_email': 'archived1@alternative.com',
        'is_active': False,
    },
]


@pytest.mark.django_db
@pytest.mark.parametrize(
    'email,expected_matching_status,match_on_alternative',
    (
        # same case, match on email
        ('unique1@primary.com', MatchingStatus.matched, False),
        # same case, match on email_alternative
        ('unique1@alternative.com', MatchingStatus.matched, True),
        # different case, match on email
        ('UNIQUE1@PRIMARY.COM', MatchingStatus.matched, False),
        # different case, match on email_alternative
        ('UNIQUE1@ALTERNATIVE.COM', MatchingStatus.matched, True),
        # different
        ('UNIQUE@COMPANY.IO', MatchingStatus.unmatched, None),
        # duplicate on email
        ('duplicate@primary.com', MatchingStatus.multiple_matches, None),
        # duplicate on email_alternative
        ('duplicate@alternative.com', MatchingStatus.multiple_matches, None),
        # archived contact ignored (email value specified)
        ('archived1@primary.com', MatchingStatus.unmatched, None),
        # archived contact ignored (email_alternative value specified)
        ('archived1@alternative.com', MatchingStatus.unmatched, None),
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

    assert actual_matching_status == expected_matching_status

    if actual_matching_status == MatchingStatus.matched:
        assert contact
        actual_email = contact.email_alternative if match_on_alternative else contact.email
        assert actual_email.lower() == email.lower()
    else:
        assert not contact


@pytest.mark.django_db
@pytest.mark.parametrize(
    'email,expected_matching_status,match_on_alternative',
    (
        # same case, match on email
        ('unique1@primary.com', MatchingStatus.matched, False),
        # same case, match on contact_email
        ('unique1@alternative.com', MatchingStatus.matched, True),
        # different case, match on email
        ('UNIQUE1@PRIMARY.COM', MatchingStatus.matched, False),
        # different case, match on contact_email
        ('UNIQUE1@ALTERNATIVE.COM', MatchingStatus.matched, True),
        # different
        ('UNIQUE@COMPANY.IO', MatchingStatus.unmatched, None),
        # duplicate on contact_email
        ('duplicate@alternative.com', MatchingStatus.multiple_matches, None),
        # inactive adviser ignored (email value specified)
        ('archived1@primary.com', MatchingStatus.unmatched, None),
        # inactive adviser ignored (contact_email value specified)
        ('archived1@alternative.com', MatchingStatus.unmatched, None),
    ),
)
def test_find_active_adviser_by_email_address(
    email,
    expected_matching_status,
    match_on_alternative,
):
    """Test finding a contact by email address for various scenarios."""
    for factory_kwargs in EMAIL_MATCHING_ADVISER_TEST_DATA:
        AdviserFactory(**factory_kwargs)

    adviser, actual_matching_status = find_active_adviser_by_email_address(email)

    assert actual_matching_status == expected_matching_status

    if actual_matching_status == MatchingStatus.matched:
        assert adviser
        actual_email = adviser.contact_email if match_on_alternative else adviser.email
        assert actual_email.lower() == email.lower()
    else:
        assert not adviser
