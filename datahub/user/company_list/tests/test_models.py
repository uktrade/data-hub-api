import pytest
from django.db import IntegrityError

from datahub.company.test.factories import AdviserFactory
from datahub.user.company_list.tests.factories import CompanyListFactory


@pytest.mark.django_db
class TestCompanyList:
    """Tests for the CompanyList model."""

    def test_cannot_have_multiple_legacy_default_lists_for_the_same_adviser(self):
        """
        Test that multiple lists for the same adviser are blocked when
        is_legacy_default=True.
        """
        # Create a company list unrelated to the adviser
        CompanyListFactory(is_legacy_default=True)

        adviser = AdviserFactory()
        CompanyListFactory(adviser=adviser, is_legacy_default=True)
        with pytest.raises(IntegrityError):
            CompanyListFactory(adviser=adviser, is_legacy_default=True)

    def test_cannot_have_non_legacy_default_list(self):
        """
        Test that is_legacy_default=False is not allowed.

        This is while the list field is being populated on CompanyListItem objects.
        """
        with pytest.raises(IntegrityError):
            CompanyListFactory(is_legacy_default=False)
