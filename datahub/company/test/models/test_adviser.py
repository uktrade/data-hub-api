import pytest

from datahub.company.test.factories import AdviserFactory


@pytest.mark.parametrize(
    'email, domain',
    (
        ('adviser@dit.gov.uk', 'dit.gov.uk'),
        # Emails can have @ if in quotes
        ('"adviser@dit"@dit.gov.uk', 'dit.gov.uk'),
        # Domain may not have a .
        ('adviser@dit', 'dit'),
        # Domain may have different case
        ('adviser@Dit.gov.uk', 'dit.gov.uk'),
        ('adviser@DIT.GOV.UK', 'dit.gov.uk'),
        # Invalid email
        ('adviser', None),
    ),
)
def test_get_email_domain(email, domain, db):
    """
    Test that the `Adviser.get_email_domain` method
    returns the domain for the given adviser's email.
    """
    adviser = AdviserFactory(email=email, contact_email=email)
    assert adviser.get_email_domain() == domain
