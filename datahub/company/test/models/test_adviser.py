import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

from datahub.company.models import Advisor
from datahub.company.test.factories import AdviserFactory

pytestmark = pytest.mark.django_db


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


@pytest.mark.parametrize(
    'sso_email_user_id',
    (
        'test@dit.gov.uk',
        None,
    ),
)
def test_adviser_sso_email_user_id_can_store_email_or_none(sso_email_user_id):
    """Test that SSO email user ID can store email or None."""
    assert Advisor.objects.count() == 0
    AdviserFactory(sso_email_user_id=sso_email_user_id)
    assert Advisor.objects.filter(sso_email_user_id=sso_email_user_id).exists()


def test_adviser_sso_email_user_id_is_validated():
    """Test that SSO email user ID is being validated."""
    adviser = Advisor.objects.create()
    adviser.sso_email_user_id = 'lorem ipsum'
    with pytest.raises(ValidationError) as excinfo:
        adviser.full_clean()
    assert dict(excinfo.value)['sso_email_user_id'] == ['Enter a valid email address.']


def test_adviser_sso_email_user_id_unique_constraint():
    """Test that SSO email user ID unique constraint."""
    duplicate_email = 'test@dit.gov.uk'
    # The `AdviserFactory` is configured to use `get_or_create` instead of `create`
    Advisor.objects.create(email='a@a.a', sso_email_user_id=duplicate_email)
    with pytest.raises(IntegrityError) as excinfo:
        Advisor.objects.create(email='b@b.b', sso_email_user_id=duplicate_email)
    assert (
        'duplicate key value violates unique constraint "company_advisor_sso_email_user_id_key"'
    ) in str(excinfo.value)
