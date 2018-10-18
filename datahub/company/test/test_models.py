import pytest
from django.conf import settings

from datahub.company.models import Company
from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory

# mark the whole module for db use
pytestmark = pytest.mark.django_db


def test_company_can_have_one_list_owner_assigned():
    """Test that company can have one list owner assigned."""
    company = CompanyFactory()
    adviser = AdviserFactory()

    assert company.one_list_account_owner is None  # Test that it's nullable

    company.one_list_account_owner = adviser
    company.save()

    # re-fetch object for completeness
    company_refetch = Company.objects.get(pk=str(company.pk))

    assert company_refetch.one_list_account_owner_id == adviser.pk


def test_company_get_absolute_url():
    """Test that Company.get_absolute_url() returns the correct URL."""
    company = CompanyFactory.build()
    assert company.get_absolute_url() == (
        f'{settings.DATAHUB_FRONTEND_URL_PREFIXES["company"]}/{company.pk}'
    )


def test_contact_get_absolute_url():
    """Test that Contact.get_absolute_url() returns the correct URL."""
    contact = ContactFactory.build()
    assert contact.get_absolute_url() == (
        f'{settings.DATAHUB_FRONTEND_URL_PREFIXES["contact"]}/{contact.pk}'
    )
