import pytest

from datahub.company.contact_matching import (
    ContactMatchingStatus,
    find_active_contact_by_email_address,
    MatchStrategy,
)
from datahub.company.test.factories import ContactFactory
from datahub.interaction.test.factories import CompanyInteractionFactory


EMAIL_MATCHING_CONTACT_TEST_DATA = [
    {
        'email': 'unique1@primary.com',
        'archived': False,
    },
    {
        'email': 'duplicate@primary.com',
        'archived': False,
        'interactions': 10,
    },
    {
        'email': 'duplicate@primary.com',
        'archived': False,
    },
    {
        'email': 'unique2@primary.com',
        'archived': False,
        'interactions': 10,
    },
    {
        'email': 'unique3@primary.com',
        'archived': False,
    },
    {
        'email': 'archived1@primary.com',
        'archived': True,
    },
]


@pytest.mark.django_db
@pytest.mark.parametrize(
    'email,expected_matching_status,match_strategy',
    (
        # same case, match on email
        ('unique1@primary.com', ContactMatchingStatus.matched, MatchStrategy.DEFAULT),
        # different case, match on email
        ('UNIQUE1@PRIMARY.COM', ContactMatchingStatus.matched, MatchStrategy.DEFAULT),
        # different
        ('UNIQUE@COMPANY.IO', ContactMatchingStatus.unmatched, MatchStrategy.DEFAULT),
        # duplicate on email
        ('duplicate@primary.com', ContactMatchingStatus.multiple_matches, MatchStrategy.DEFAULT),
        # archived contact ignored (email value specified)
        ('archived1@primary.com', ContactMatchingStatus.unmatched, MatchStrategy.DEFAULT),
        # same case, match on email
        ('unique1@primary.com', ContactMatchingStatus.matched, MatchStrategy.MAX_INTERACTIONS),
        # different case, match on email
        ('UNIQUE1@PRIMARY.COM', ContactMatchingStatus.matched, MatchStrategy.MAX_INTERACTIONS),
        # different
        ('UNIQUE@COMPANY.IO', ContactMatchingStatus.unmatched, MatchStrategy.MAX_INTERACTIONS),
        # duplicate on email
        ('duplicate@primary.com', ContactMatchingStatus.matched, MatchStrategy.MAX_INTERACTIONS),
        # archived contact ignored (email value specified)
        ('archived1@primary.com', ContactMatchingStatus.unmatched, MatchStrategy.MAX_INTERACTIONS),
    ),
)
def test_find_active_contact_by_email_address(
    email,
    expected_matching_status,
    match_strategy,
):
    """Test finding a contact by email address for various scenarios."""
    for factory_kwargs in EMAIL_MATCHING_CONTACT_TEST_DATA:
        interaction_count = 0
        if factory_kwargs.get('interactions'):
            interaction_count = factory_kwargs.pop('interactions')
        created_contact = ContactFactory(**factory_kwargs)
        for _ in range(interaction_count):
            CompanyInteractionFactory(contacts=[created_contact])

    contact, actual_matching_status = find_active_contact_by_email_address(email, match_strategy)

    assert actual_matching_status == expected_matching_status

    if actual_matching_status == ContactMatchingStatus.matched:
        assert contact
        assert contact.email.lower() == email.lower()
    else:
        assert not contact
