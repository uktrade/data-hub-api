import pytest

from datahub.company.models import Company
from datahub.company.test.factories import AdvisorFactory, CompanyFactory
from datahub.core import constants

# mark the whole module for db use
pytestmark = pytest.mark.django_db


def test_company_model_sets_classification_to_undefined():
    """Test setting classification to undef by default."""
    c = CompanyFactory()  # Calls save
    assert c.classification_id == constants.CompanyClassification.undefined.value.id


def test_company_can_have_one_list_owner_assigned():
    """Test that company can have one list owner assigned."""
    c = CompanyFactory()
    a = AdvisorFactory()

    assert c.one_list_account_owner is None  # Test that it's nullable

    c.one_list_account_owner = a
    c.save()

    # re-fetch object for completeness
    c2 = Company.objects.get(pk=str(c.pk))

    assert str(c2.one_list_account_owner_id) == str(a.pk)


def test_company_can_have_hierarchy():
    """Test that company can have hierarchy."""
    c1 = CompanyFactory()
    c2 = CompanyFactory()

    assert c1.parent is None
    assert c1.subsidiaries.count() == 0
    assert c2.parent is None
    assert c2.subsidiaries.count() == 0

    c2.parent = c1
    c2.save()

    c1.refresh_from_db()
    c2.refresh_from_db()

    assert c2.parent is c1
    assert c2 in c1.subsidiaries.all()
