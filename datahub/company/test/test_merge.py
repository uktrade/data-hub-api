from datetime import datetime
from itertools import chain
from unittest.mock import Mock

import pytest
from django.utils.timezone import utc
from freezegun import freeze_time

from datahub.company.merge import (
    DuplicateCompanyMerger,
    MergeNotAllowedError,
    MergeResult,
    MoveEntry,
)
from datahub.company.models import Company, Contact
from datahub.company.test.factories import (
    AdviserFactory,
    ArchivedCompanyFactory,
    CompanyFactory,
    ContactFactory,
)
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

    @pytest.mark.parametrize('source_num_interactions', (0, 1, 3))
    @pytest.mark.parametrize('source_num_contacts', (0, 1, 3))
    def test_merge_succeeds(self, source_num_interactions, source_num_contacts):
        """
        Tests that perform_merge() moves contacts and interactions to the target company,
        and marks the source company as archived and transferred.
        """
        creation_time = datetime(2010, 12, 1, 15, 0, 10, tzinfo=utc)
        with freeze_time(creation_time):
            source_company = _company_factory(source_num_interactions, source_num_contacts)
        target_company = CompanyFactory()
        user = AdviserFactory()

        source_interactions = list(source_company.interactions.all())
        source_contacts = list(source_company.contacts.all())
        # Each interaction has a contact, so actual number of contacts is
        # source_num_interactions + source_num_contacts
        assert len(source_contacts) == source_num_interactions + source_num_contacts

        merger = DuplicateCompanyMerger(source_company, target_company)
        merge_time = datetime(2011, 2, 1, 14, 0, 10, tzinfo=utc)

        with freeze_time(merge_time):
            result = merger.perform_merge(user)

        assert result == MergeResult(
            num_interactions_moved=len(source_interactions),
            num_contacts_moved=len(source_contacts),
        )

        for obj in chain(source_interactions, source_contacts):
            obj.refresh_from_db()

        assert all(obj.company == target_company for obj in source_interactions)
        assert all(obj.modified_on == creation_time for obj in source_interactions)
        assert all(obj.company == target_company for obj in source_contacts)
        assert all(obj.modified_on == creation_time for obj in source_contacts)

        source_company.refresh_from_db()

        assert source_company.archived
        assert source_company.archived_by == user
        assert source_company.archived_on == merge_time
        assert source_company.archived_reason == (
            f'This record is no longer in use and its data has been transferred '
            f'to {target_company} for the following reason: Duplicate record.'
        )
        assert source_company.modified_by == user
        assert source_company.modified_on == merge_time
        assert source_company.transfer_reason == Company.TRANSFER_REASONS.duplicate
        assert source_company.transferred_by == user
        assert source_company.transferred_on == merge_time
        assert source_company.transferred_to == target_company

    def test_merge_fails_when_not_allowed(self, monkeypatch):
        """
        Test that perform_merge() raises DuplicateCompanyMerger when the merge is not
        allowed.
        """
        monkeypatch.setattr(DuplicateCompanyMerger, 'is_valid', Mock(return_value=False))

        source_company = CompanyFactory()
        target_company = CompanyFactory()
        user = AdviserFactory()
        merger = DuplicateCompanyMerger(source_company, target_company)
        with pytest.raises(MergeNotAllowedError):
            merger.perform_merge(user)


def _company_factory(num_interactions, num_contacts):
    """Factory for a company that has companies and interactions."""
    company = CompanyFactory()
    ContactFactory.create_batch(num_contacts, company=company)
    CompanyInteractionFactory.create_batch(num_interactions, company=company)
    return company
