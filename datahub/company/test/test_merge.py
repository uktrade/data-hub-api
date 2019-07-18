from datetime import datetime
from itertools import chain
from unittest.mock import patch

import pytest
from django.utils.timezone import utc
from freezegun import freeze_time

from datahub.company.merge import (
    get_planned_changes,
    INVESTMENT_PROJECT_COMPANY_FIELDS,
    merge_companies,
    MergeNotAllowedError,
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
from datahub.investment.project.models import InvestmentProject
from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.omis.order.models import Order
from datahub.omis.order.test.factories import OrderFactory
from datahub.user.company_list.models import CompanyListItem
from datahub.user.company_list.tests.factories import CompanyListItemFactory


@pytest.fixture
def unrelated_objects():
    """
    Create some objects not related to a known company.

    This is used in tests below to make sure objects unrelated to the company being merged
    do not affect the counts of objects that will be affected by the merge.
    """
    ContactFactory.create_batch(5)
    CompanyInteractionFactory.create_batch(5)
    OrderFactory.create_batch(5)
    InvestmentProjectFactory.create_batch(5)


def company_with_interactions_and_contacts_factory():
    """
    Factory for a company with interactions (and hence contacts, as interactions have contacts).
    """
    company = CompanyFactory()
    CompanyInteractionFactory.create_batch(4, company=company)
    return company


def company_with_company_list_items_factory():
    """Factory for a company that is on users' personal company lists."""
    company = CompanyFactory()
    CompanyListItemFactory.create_batch(3, company=company)
    return company


def company_with_contacts_factory():
    """Factory for a company with contacts."""
    company = CompanyFactory()
    ContactFactory.create_batch(3, company=company)
    return company


def company_with_orders_factory():
    """Factory for a company with orders."""
    company = CompanyFactory()
    OrderFactory.create_batch(3, company=company)
    return company


def company_with_investment_projects_factory():
    """Factory for a company with investment projects."""
    company = CompanyFactory()
    for field in INVESTMENT_PROJECT_COMPANY_FIELDS:
        InvestmentProjectFactory(**{field: company})
    return company


@pytest.mark.django_db
class TestDuplicateCompanyMerger:
    """Tests DuplicateCompanyMerger."""

    @pytest.mark.parametrize(
        'source_company_factory,expected_result,expected_should_archive',
        (
            (
                CompanyFactory,
                {
                    CompanyListItem: {'company': 0},
                    Contact: {'company': 0},
                    Interaction: {'company': 0},
                    InvestmentProject: {
                        field: 0 for field in INVESTMENT_PROJECT_COMPANY_FIELDS
                    },
                    Order: {'company': 0},
                },
                True,
            ),
            (
                company_with_interactions_and_contacts_factory,
                {
                    CompanyListItem: {'company': 0},
                    Contact: {'company': 4},
                    Interaction: {'company': 4},
                    InvestmentProject: {
                        field: 0 for field in INVESTMENT_PROJECT_COMPANY_FIELDS
                    },
                    Order: {'company': 0},
                },
                True,
            ),
            (
                company_with_contacts_factory,
                {
                    CompanyListItem: {'company': 0},
                    Contact: {'company': 3},
                    Interaction: {'company': 0},
                    InvestmentProject: {
                        field: 0 for field in INVESTMENT_PROJECT_COMPANY_FIELDS
                    },
                    Order: {'company': 0},
                },
                True,
            ),
            (
                company_with_company_list_items_factory,
                {
                    CompanyListItem: {'company': 3},
                    Contact: {'company': 0},
                    Interaction: {'company': 0},
                    InvestmentProject: {
                        field: 0 for field in INVESTMENT_PROJECT_COMPANY_FIELDS
                    },
                    Order: {'company': 0},
                },
                True,
            ),
            (
                company_with_investment_projects_factory,
                {
                    CompanyListItem: {'company': 0},
                    Contact: {'company': 0},
                    Interaction: {'company': 0},
                    InvestmentProject: {
                        field: 1 for field in INVESTMENT_PROJECT_COMPANY_FIELDS
                    },
                    Order: {'company': 0},
                },
                True,
            ),
            (
                company_with_orders_factory,
                {
                    CompanyListItem: {'company': 0},
                    Contact: {'company': 3},
                    Interaction: {'company': 0},
                    InvestmentProject: {
                        field: 0 for field in INVESTMENT_PROJECT_COMPANY_FIELDS
                    },
                    Order: {'company': 3},
                },
                True,
            ),
            (
                ArchivedCompanyFactory,
                {
                    CompanyListItem: {'company': 0},
                    Contact: {'company': 0},
                    Interaction: {'company': 0},
                    InvestmentProject: {
                        field: 0 for field in INVESTMENT_PROJECT_COMPANY_FIELDS
                    },
                    Order: {'company': 0},
                },
                False,
            ),
        ),
    )
    @pytest.mark.usefixtures('unrelated_objects')
    def test_get_planned_changes(
        self,
        source_company_factory,
        expected_result,
        expected_should_archive,
    ):
        """
        Tests that get_planned_changes() returns the correct planned changes for various
        cases.
        """
        source_company = source_company_factory()
        merge_results = get_planned_changes(source_company)

        expected_planned_merge_results = (expected_result, expected_should_archive)
        assert merge_results == expected_planned_merge_results

    @pytest.mark.parametrize('source_num_interactions', (0, 1, 3))
    @pytest.mark.parametrize('source_num_contacts', (0, 1, 3))
    @pytest.mark.parametrize('source_num_orders', (0, 1, 3))
    @pytest.mark.parametrize('source_num_company_list_items', (0, 1, 3))
    @pytest.mark.usefixtures('unrelated_objects')
    def test_merge_interactions_contacts_succeeds(
            self,
            source_num_interactions,
            source_num_contacts,
            source_num_orders,
            source_num_company_list_items,
    ):
        """
        Tests that perform_merge() moves contacts and interactions to the target company,
        and marks the source company as archived and transferred.
        """
        creation_time = datetime(2010, 12, 1, 15, 0, 10, tzinfo=utc)
        with freeze_time(creation_time):
            source_company = _company_factory(
                source_num_interactions,
                source_num_contacts,
                source_num_orders,
                source_num_company_list_items,
            )
        target_company = CompanyFactory()
        user = AdviserFactory()

        source_interactions = list(source_company.interactions.all())
        source_contacts = list(source_company.contacts.all())
        source_orders = list(source_company.orders.all())
        source_company_list_items = list(source_company.company_list_items.all())

        # Each interaction and order has a contact, so actual number of contacts is
        # source_num_interactions + source_num_contacts + source_num_orders
        assert len(source_contacts) == (
            source_num_interactions + source_num_contacts + source_num_orders
        )

        merge_time = datetime(2011, 2, 1, 14, 0, 10, tzinfo=utc)

        with freeze_time(merge_time):
            result = merge_companies(source_company, target_company, user)

        assert result == {
            CompanyListItem: {'company': len(source_company_list_items)},
            Contact: {'company': len(source_contacts)},
            Interaction: {'company': len(source_interactions)},
            InvestmentProject: {
                field: 0 for field in INVESTMENT_PROJECT_COMPANY_FIELDS
            },
            Order: {'company': len(source_orders)},
        }

        for obj in chain(source_interactions, source_contacts, source_orders):
            obj.refresh_from_db()

        assert all(obj.company == target_company for obj in source_interactions)
        assert all(obj.modified_on == creation_time for obj in source_interactions)
        assert all(obj.company == target_company for obj in source_contacts)
        assert all(obj.modified_on == creation_time for obj in source_contacts)
        assert all(obj.company == target_company for obj in source_orders)
        assert all(obj.modified_on == creation_time for obj in source_orders)

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

    @pytest.mark.parametrize(
        'fields',
        (
            (),
            ('investor_company',),
            ('intermediate_company',),
            ('uk_company',),
            ('investor_company', 'intermediate_company'),
            ('investor_company', 'uk_company'),
            ('intermediate_company', 'uk_company'),
            ('investor_company', 'intermediate_company', 'uk_company'),
        ),
    )
    @pytest.mark.usefixtures('unrelated_objects')
    def test_merge_investment_projects_succeeds(self, fields):
        """
        Tests that perform_merge() moves investment projects to the target company and marks the
        source company as archived and transferred.
        """
        creation_time = datetime(2010, 12, 1, 15, 0, 10, tzinfo=utc)
        with freeze_time(creation_time):
            source_company = CompanyFactory()
            investment_project = InvestmentProjectFactory(
                **{field: source_company for field in fields},
            )

        target_company = CompanyFactory()
        user = AdviserFactory()

        merge_time = datetime(2011, 2, 1, 14, 0, 10, tzinfo=utc)

        with freeze_time(merge_time):
            result = merge_companies(source_company, target_company, user)

        other_fields = set(INVESTMENT_PROJECT_COMPANY_FIELDS) - set(fields)

        assert result == {
            # each interaction has a contact, that's why 4 contacts should be moved
            CompanyListItem: {'company': 0},
            Contact: {'company': 0},
            Interaction: {'company': 0},
            InvestmentProject: {
                **{
                    field: 1
                    for field in fields
                },
                **{
                    field: 0
                    for field in other_fields
                },
            },
            Order: {'company': 0},
        }

        investment_project.refresh_from_db()

        assert all(getattr(investment_project, field) == target_company for field in fields)
        assert all(getattr(investment_project, field) != target_company for field in other_fields)
        assert all(getattr(investment_project, field) != source_company for field in other_fields)

        assert investment_project.modified_on == creation_time

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

    @pytest.mark.parametrize(
        'valid_source,valid_target',
        (
            (False, True),
            (True, False),
            (False, False),
        ),
    )
    @patch('datahub.company.merge.is_company_a_valid_merge_target')
    @patch('datahub.company.merge.is_company_a_valid_merge_source')
    def test_merge_fails_when_not_allowed(
        self,
        is_company_a_valid_merge_source_mock,
        is_company_a_valid_merge_target_mock,
        valid_source,
        valid_target,
    ):
        """
        Test that perform_merge() raises MergeNotAllowedError when the merge is not
        allowed.
        """
        is_company_a_valid_merge_source_mock.return_value = valid_source
        is_company_a_valid_merge_target_mock.return_value = valid_target

        source_company = CompanyFactory()
        target_company = CompanyFactory()
        user = AdviserFactory()
        with pytest.raises(MergeNotAllowedError):
            merge_companies(source_company, target_company, user)


def _company_factory(num_interactions, num_contacts, num_orders, num_company_list_items):
    """Factory for a company that has companies, interactions and OMIS orders."""
    company = CompanyFactory()
    ContactFactory.create_batch(num_contacts, company=company)
    CompanyInteractionFactory.create_batch(num_interactions, company=company)
    OrderFactory.create_batch(num_orders, company=company)
    CompanyListItemFactory.create_batch(num_company_list_items, company=company)
    return company
