import pytest

from datahub.company.merge import DuplicateCompanyMerger, MoveEntry
from datahub.company.models import Contact
from datahub.company.test.factories import ArchivedCompanyFactory, CompanyFactory, ContactFactory
from datahub.interaction.models import Interaction
from datahub.interaction.test.factories import CompanyInteractionFactory


def company_with_interactions_and_contacts_factory():
    """
    Factory for a company with interactions (and hence contacts, as interactions have contacts).
    """
    company = CompanyFactory()
    CompanyInteractionFactory.create_batch(4, company=company)
    return company


def company_with_contacts_factory():
    """Factory for a company with contacts."""
    company = CompanyFactory()
    ContactFactory.create_batch(3, company=company)
    return company


@pytest.mark.django_db
class TestDuplicateCompanyMerger:
    """Tests DuplicateCompanyMerger."""

    @pytest.mark.parametrize(
        'source_company_factory,expected_move_entries,expected_should_archive',
        (
            (CompanyFactory, [], True),
            (
                company_with_interactions_and_contacts_factory,
                [MoveEntry(4, Contact._meta), MoveEntry(4, Interaction._meta)],
                True,
            ),
            (company_with_contacts_factory, [MoveEntry(3, Contact._meta)], True),
            (ArchivedCompanyFactory, [], False),
        ),
    )
    def test_get_planned_changes(
        self,
        source_company_factory,
        expected_move_entries,
        expected_should_archive,
    ):
        """
        Tests that get_planned_changes() returns the correct planned changes for various
        cases.
        """
        source_company = source_company_factory()
        target_company = CompanyFactory()
        duplicate_merger = DuplicateCompanyMerger(source_company, target_company)

        expected_planned_changes = (expected_move_entries, expected_should_archive)
        assert duplicate_merger.get_planned_changes() == expected_planned_changes
