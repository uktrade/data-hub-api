from datetime import datetime, timezone
from unittest.mock import patch

import pytest
import reversion
from freezegun import freeze_time

from datahub.company.merge import (
    get_planned_changes,
    MergeNotAllowedError,
)
from datahub.company.merge_company import (
    ALLOWED_RELATIONS_FOR_MERGING,
    INVESTMENT_PROJECT_COMPANY_FIELDS,
    merge_companies,
    MERGE_CONFIGURATION,
    rollback_merge_companies,
)
from datahub.company.models import (
    Company,
    CompanyExport,
    Contact,
    Objective,
    OneListCoreTeamMember,
)
from datahub.company.test.factories import (
    AdviserFactory,
    ArchivedCompanyFactory,
    CompanyExportCountryFactory,
    CompanyExportCountryHistoryFactory,
    CompanyFactory,
    ContactFactory,
    ExportFactory,
    ObjectiveFactory,
    OneListCoreTeamMemberFactory,
)
from datahub.company_activity.models import CompanyActivity
from datahub.company_referral.models import CompanyReferral
from datahub.company_referral.test.factories import CompanyReferralFactory
from datahub.export_win.models import LegacyExportWinsToDataHubCompany
from datahub.export_win.test.factories import LegacyExportWinsToDataHubCompanyFactory
from datahub.interaction.models import Interaction
from datahub.interaction.test.factories import CompanyInteractionFactory
from datahub.investment.investor_profile.models import LargeCapitalInvestorProfile
from datahub.investment.investor_profile.test.factories import (
    CompleteLargeCapitalInvestorProfileFactory,
)
from datahub.investment.opportunity.models import LargeCapitalOpportunity
from datahub.investment.opportunity.test.factories import LargeCapitalOpportunityFactory
from datahub.investment.project.models import InvestmentProject
from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.investment_lead.models import EYBLead
from datahub.investment_lead.test.factories import EYBLeadFactory
from datahub.omis.order.models import Order
from datahub.omis.order.test.factories import OrderFactory
from datahub.reminder.models import (
    NewExportInteractionReminder,
    NoRecentExportInteractionReminder,
)
from datahub.reminder.test.factories import (
    NewExportInteractionReminderFactory,
    NoRecentExportInteractionReminderFactory,
)
from datahub.task.models import Task
from datahub.task.test.factories import TaskFactory
from datahub.user.company_list.models import CompanyListItem, PipelineItem
from datahub.user.company_list.test.factories import (
    CompanyListFactory,
    CompanyListItemFactory,
    PipelineItemFactory,
)


@pytest.fixture
def unrelated_objects():
    """
    Create some objects not related to a known company.

    This is used in tests below to make sure objects unrelated to the company being merged
    do not affect the counts of objects that will be affected by the merge.
    """
    ContactFactory.create_batch(2)
    CompanyReferralFactory.create_batch(2)
    CompanyInteractionFactory.create_batch(2)
    OrderFactory.create_batch(2)
    InvestmentProjectFactory.create_batch(2)


def company_with_interactions_and_contacts_factory():
    """
    Factory for a company with interactions (and hence contacts, as interactions have contacts).
    """
    company = CompanyFactory()
    CompanyInteractionFactory.create_batch(3, company=company)
    return company


def company_with_company_list_items_factory():
    """Factory for a company that is on users' personal company lists."""
    company = CompanyFactory()
    CompanyListItemFactory.create_batch(3, company=company)
    return company


def company_with_pipeline_items_factory():
    """Factory for a company that is on users' personal pipeline."""
    company = CompanyFactory()
    PipelineItemFactory.create_batch(3, company=company)
    return company


def company_with_contacts_factory():
    """Factory for a company with contacts."""
    company = CompanyFactory()
    ContactFactory.create_batch(3, company=company)
    return company


def company_with_referrals_factory():
    """
    Factory for a company with referrals.

    No company contacts are created to simplify testing.
    """
    company = CompanyFactory()
    CompanyReferralFactory.create_batch(3, company=company, contact=None)
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

    # The model and its fields related to a Company and a count for
    # how many fields were merged during the company merge.
    # i.e. {..., Contact: {'company': 0} }
    base_expected_results = {
        configuration.model: {field: 0 for field in configuration.fields}
        for configuration in MERGE_CONFIGURATION
    }

    @pytest.mark.parametrize(
        'source_company_factory,expected_result,expected_should_archive',
        (
            (
                CompanyFactory,
                base_expected_results,
                True,
            ),
            (
                company_with_interactions_and_contacts_factory,
                {
                    **base_expected_results,
                    CompanyActivity: {'company': 3},
                    Contact: {'company': 3},
                    Interaction: {'company': 3, 'companies': 3},
                },
                True,
            ),
            (
                company_with_contacts_factory,
                {
                    **base_expected_results,
                    Contact: {'company': 3},
                },
                True,
            ),
            (
                company_with_referrals_factory,
                {
                    **base_expected_results,
                    CompanyActivity: {'company': 3},
                    CompanyReferral: {'company': 3},
                },
                True,
            ),
            (
                company_with_company_list_items_factory,
                {
                    **base_expected_results,
                    CompanyListItem: {'company': 3},
                },
                True,
            ),
            (
                company_with_pipeline_items_factory,
                {
                    **base_expected_results,
                    PipelineItem: {'company': 3},
                },
                True,
            ),
            (
                company_with_investment_projects_factory,
                {
                    **base_expected_results,
                    CompanyActivity: {'company': 1},
                    InvestmentProject: {
                        field: 1 for field in INVESTMENT_PROJECT_COMPANY_FIELDS
                    },

                },
                True,
            ),
            (
                company_with_orders_factory,
                {
                    **base_expected_results,
                    Contact: {'company': 3},
                    Order: {'company': 3},

                },
                True,
            ),
            (
                ArchivedCompanyFactory,
                {
                    **base_expected_results,
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
        merge_results = get_planned_changes(source_company, MERGE_CONFIGURATION)

        expected_planned_merge_results = (expected_result, expected_should_archive)
        assert merge_results == expected_planned_merge_results

    @pytest.mark.parametrize(
        'factory_relation_kwarg,creates_contacts',
        (
            ('num_company_list_items', False),
            ('num_contacts', True),
            ('num_interactions', True),
            ('num_orders', True),
            ('num_referrals', False),
            ('num_pipeline_items', False),
        ),
    )
    @pytest.mark.parametrize('num_related_objects', (0, 1, 3))
    @pytest.mark.usefixtures('unrelated_objects')
    def test_merge_interactions_contacts_succeeds(
            self,
            factory_relation_kwarg,
            creates_contacts,
            num_related_objects,
    ):
        """
        Tests that perform_merge() moves contacts and interactions to the target company,
        and marks the source company as archived and transferred.
        """
        creation_time = datetime(2010, 12, 1, 15, 0, 10, tzinfo=timezone.utc)
        with freeze_time(creation_time):
            source_company = _company_factory(
                **{factory_relation_kwarg: num_related_objects},
            )
        target_company = CompanyFactory()
        user = AdviserFactory()

        source_company_activity_items = list(source_company.activities.all())
        source_interactions = list(source_company.interactions.all())
        source_contacts = list(source_company.contacts.all())
        source_orders = list(source_company.orders.all())
        source_referrals = list(source_company.referrals.all())
        source_company_list_items = list(source_company.company_list_items.all())
        source_pipeline_list_items = list(source_company.pipeline_list_items.all())

        # Each interaction and order has a contact, so actual number of contacts is
        # source_num_interactions + source_num_contacts + source_num_orders
        assert len(source_contacts) == (num_related_objects if creates_contacts else 0)

        merge_time = datetime(2011, 2, 1, 14, 0, 10, tzinfo=timezone.utc)

        with freeze_time(merge_time):
            result = merge_companies(source_company, target_company, user)

        assert result == {
            **self.base_expected_results,
            CompanyActivity: {'company': len(source_company_activity_items)},
            CompanyListItem: {'company': len(source_company_list_items)},
            CompanyReferral: {'company': len(source_referrals)},
            Contact: {'company': len(source_contacts)},
            Interaction: {
                'company': len(source_interactions),
                'companies': len(source_interactions),
            },
            Order: {'company': len(source_orders)},
            PipelineItem: {'company': len(source_pipeline_list_items)},
        }

        source_related_objects = [
            *source_company_list_items,
            *source_contacts,
            *source_interactions,
            *source_orders,
            *source_referrals,
            *source_pipeline_list_items,
        ]

        for obj in source_related_objects:
            obj.refresh_from_db()

        assert all(obj.company == target_company for obj in source_related_objects)
        assert all(obj.modified_on == merge_time for obj in source_related_objects)

        source_company.refresh_from_db()

        assert source_company.archived
        assert source_company.archived_by == user
        assert source_company.archived_on == merge_time
        assert source_company.archived_reason == (
            'This record is no longer in use and its data has been transferred '
            f'to {target_company} for the following reason: Duplicate record.'
        )
        assert source_company.modified_by == user
        assert source_company.modified_on == merge_time
        assert source_company.transfer_reason == Company.TransferReason.DUPLICATE
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
        creation_time = datetime(2010, 12, 1, 15, 0, 10, tzinfo=timezone.utc)
        with freeze_time(creation_time):
            source_company = CompanyFactory()
            investment_project = InvestmentProjectFactory(
                **{field: source_company for field in fields},
            )

        target_company = CompanyFactory()
        user = AdviserFactory()

        merge_time = datetime(2011, 2, 1, 14, 0, 10, tzinfo=timezone.utc)

        with freeze_time(merge_time):
            result = merge_companies(source_company, target_company, user)

        other_fields = set(INVESTMENT_PROJECT_COMPANY_FIELDS) - set(fields)

        company = {'company': 0}
        # CompanyActivity is created if an investment project investor_company is saved
        if 'investor_company' in fields:
            company = {'company': 1}

        assert result == {
            **self.base_expected_results,
            # each interaction has a contact, that's why 4 contacts should be moved
            CompanyActivity: company,
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
        }

        investment_project.refresh_from_db()

        assert all(getattr(investment_project, field) == target_company for field in fields)
        assert all(getattr(investment_project, field) != target_company for field in other_fields)
        assert all(getattr(investment_project, field) != source_company for field in other_fields)

        # Only check that the modified field is updated if the investment project
        # is linked to the source company
        if fields:
            assert investment_project.modified_on == merge_time

        source_company.refresh_from_db()

        assert source_company.archived
        assert source_company.archived_by == user
        assert source_company.archived_on == merge_time
        assert source_company.archived_reason == (
            'This record is no longer in use and its data has been transferred '
            f'to {target_company} for the following reason: Duplicate record.'
        )
        assert source_company.modified_by == user
        assert source_company.modified_on == merge_time
        assert source_company.transfer_reason == Company.TransferReason.DUPLICATE
        assert source_company.transferred_by == user
        assert source_company.transferred_on == merge_time
        assert source_company.transferred_to == target_company

    def test_merge_when_both_companies_on_same_company_list(self):
        """
        Test that if both the source and target company are on the same company list,
        the merge is successful and the two list items are also merged.
        """
        source_company = CompanyFactory()
        target_company = CompanyFactory()
        company_list = CompanyListFactory()

        CompanyListItemFactory(list=company_list, company=source_company)
        CompanyListItemFactory(list=company_list, company=target_company)

        user = AdviserFactory()

        merge_companies(source_company, target_company, user)

        assert not CompanyListItem.objects.filter(
            list=company_list,
            company=source_company,
        ).exists()
        assert CompanyListItem.objects.filter(list=company_list, company=target_company).exists()

    @pytest.mark.parametrize(
        'source_status,target_status',
        (
            (PipelineItem.Status.LEADS, PipelineItem.Status.LEADS),
            (PipelineItem.Status.LEADS, PipelineItem.Status.IN_PROGRESS),
        ),
    )
    def test_merge_when_both_companies_are_on_pipeline_for_same_adviser(
        self,
        source_status,
        target_status,
    ):
        """
        Test that both source and target company are on pipeline for the same adviser
        and same status. And the merge is successful.
        """
        adviser = AdviserFactory()
        source_company = CompanyFactory()
        target_company = CompanyFactory()

        PipelineItemFactory(
            adviser=adviser,
            company=source_company,
            status=source_status,
        )
        PipelineItemFactory(
            adviser=adviser,
            company=target_company,
            status=target_status,
        )

        user = AdviserFactory()
        merge_companies(source_company, target_company, user)

        assert not PipelineItem.objects.filter(
            adviser=adviser,
            company=source_company,
        ).exists()
        assert PipelineItem.objects.filter(
            adviser=adviser,
            company=target_company,
        ).exists()

    def test_merge_when_both_companies_are_on_pipeline_diff_adviser(self):
        """
        Test that both source and target company are on pipeline with different advisers.
        Merge is successful and both items are migrated to the target company.
        """
        adviser_1 = AdviserFactory()
        adviser_2 = AdviserFactory()
        source_company = CompanyFactory()
        target_company = CompanyFactory()

        PipelineItemFactory(
            adviser=adviser_1,
            company=source_company,
            status=PipelineItem.Status.LEADS,
        )
        PipelineItemFactory(
            adviser=adviser_2,
            company=target_company,
            status=PipelineItem.Status.IN_PROGRESS,
        )

        user = AdviserFactory()
        merge_companies(source_company, target_company, user)

        assert not PipelineItem.objects.filter(
            adviser=adviser_1,
            company=source_company,
        ).exists()
        assert PipelineItem.objects.filter(
            adviser=adviser_1,
            company=target_company,
        ).exists()
        assert PipelineItem.objects.filter(
            adviser=adviser_2,
            company=target_company,
        ).exists()

    def test_merge_allowed_when_source_company_has_export_countries(self):
        """Test that merging is allowed if the source company has export countries."""
        source_company = CompanyFactory()
        CompanyExportCountryFactory(company=source_company)
        CompanyExportCountryHistoryFactory(company=source_company)

        target_company = CompanyFactory()
        user = AdviserFactory()

        merge_time = datetime(2011, 2, 1, 14, 0, 10, tzinfo=timezone.utc)

        with freeze_time(merge_time):
            merge_companies(source_company, target_company, user)

        source_company.refresh_from_db()

        assert source_company.archived
        assert source_company.archived_by == user
        assert source_company.archived_on == merge_time
        assert source_company.archived_reason == (
            'This record is no longer in use and its data has been transferred '
            f'to {target_company} for the following reason: Duplicate record.'
        )
        assert source_company.modified_by == user
        assert source_company.modified_on == merge_time
        assert source_company.transfer_reason == Company.TransferReason.DUPLICATE
        assert source_company.transferred_by == user
        assert source_company.transferred_on == merge_time
        assert source_company.transferred_to == target_company

    @pytest.mark.parametrize(
        'valid_source_return_value, valid_target',
        (
            ((False, ['field1', 'field2']), True),
            ((True, []), False),
            ((False, ['field1']), False),
        ),
    )
    @patch('datahub.company.merge_company.is_model_a_valid_merge_target')
    @patch('datahub.company.merge_company.is_model_a_valid_merge_source')
    def test_merge_fails_when_not_allowed(
        self,
        is_company_a_valid_merge_source_mock,
        is_company_a_valid_merge_target_mock,
        valid_source_return_value,
        valid_target,
    ):
        """
        Test that perform_merge() raises MergeNotAllowedError when the merge is not
        allowed.
        """
        is_company_a_valid_merge_source_mock.return_value = valid_source_return_value
        is_company_a_valid_merge_target_mock.return_value = valid_target

        source_company = CompanyFactory()
        target_company = CompanyFactory()
        user = AdviserFactory()
        with pytest.raises(MergeNotAllowedError):
            merge_companies(source_company, target_company, user)

    def test_rollback(self):
        """
        Test that rollback_merge_companies() rolls back a merge of companies
        """
        with reversion.create_revision():
            source_company = _company_factory(2, 2, 2, 2, 2, 2)
            target_company = _company_factory(3, 3, 3, 3, 3, 3)
        user = AdviserFactory()
        source_company_num_contacts = source_company.contacts.count()
        target_company_num_contacts = target_company.contacts.count()

        # Briefly make sure we really have merged the companies, so the late
        # assertions don't just pass because the companeis have never been merged
        merge_companies(source_company, target_company, user)
        source_company.refresh_from_db()
        target_company.refresh_from_db()
        assert not source_company.interactions.exists()
        assert not source_company.contacts.exists()
        assert not source_company.orders.exists()
        assert not source_company.referrals.exists()
        assert not source_company.company_list_items.exists()
        assert not source_company.pipeline_list_items.exists()
        assert source_company.transferred_to == target_company

        assert target_company.interactions.count() == 5
        assert target_company.contacts.count() == \
            source_company_num_contacts + target_company_num_contacts
        assert target_company.orders.count() == 5
        assert target_company.referrals.count() == 5
        assert target_company.company_list_items.count() == 5
        assert target_company.pipeline_list_items.count() == 5

        # Make sure related models are attached to the original company
        rollback_merge_companies(source_company)
        source_company.refresh_from_db()
        target_company.refresh_from_db()
        assert source_company.interactions.count() == 2
        assert source_company.contacts.count() == source_company_num_contacts
        assert source_company.orders.count() == 2
        assert source_company.referrals.count() == 2
        assert source_company.company_list_items.count() == 2
        assert source_company.pipeline_list_items.count() == 2
        assert source_company.transferred_to is None

        assert target_company.interactions.count() == 3
        assert target_company.contacts.count() == target_company_num_contacts
        assert target_company.orders.count() == 3
        assert target_company.referrals.count() == 3
        assert target_company.company_list_items.count() == 3
        assert target_company.pipeline_list_items.count() == 3

    def test_related_fields_are_versioned(self):
        for relation in ALLOWED_RELATIONS_FOR_MERGING:
            assert reversion.is_registered(relation.model), \
                f'{relation.model} is not registered with reversion'

    def test_one_list_core_team_member_merges_successfully(self):
        """
        Test merge is successful.
        If both the source and target company have the same adviser for the
        one_list_core_team_member relationship that it is not copied as duplicates
        are not allowed for the same company.
        """
        adviser = AdviserFactory()
        source_company = CompanyFactory()
        target_company = CompanyFactory()

        # Source company with same adviser as target company
        OneListCoreTeamMemberFactory(adviser=adviser, company=source_company)
        OneListCoreTeamMemberFactory(adviser=AdviserFactory(), company=source_company)

        OneListCoreTeamMemberFactory(adviser=adviser, company=target_company)

        # Target has only the 1 OneListCoreTeamMember
        assert OneListCoreTeamMember.objects.filter(
            company=target_company,
        ).count() == 1

        merge_companies(source_company, target_company, adviser)

        # Merge successful and target has 2 advisers.
        assert OneListCoreTeamMember.objects.filter(
            company=target_company,
        ).count() == 2
        # Merge successful and target does not have duplicate advisers.
        assert OneListCoreTeamMember.objects.filter(
            company=target_company,
            adviser=adviser,
        ).count() == 1

    def test_company_export_merges_successfully(self):
        """
        Test company merge successfully merges company `CompanyExport`s.
        """
        adviser = AdviserFactory()
        source_company = CompanyFactory()
        target_company = CompanyFactory()

        # Source company with export
        ExportFactory(company=source_company)

        # Target company with its own export
        ExportFactory(company=target_company)

        merge_companies(source_company, target_company, adviser)

        # Merge successful and target now has 2 company exports
        assert CompanyExport.objects.filter(
            company=target_company,
        ).count() == 2

    def test_company_objective_merges_successfully(self):
        """
        Test company merge successfully merges company `Objective`s.
        """
        adviser = AdviserFactory()
        source_company = CompanyFactory()
        target_company = CompanyFactory()

        # Source company with objective
        ObjectiveFactory(company=source_company)

        # Target company with its own objective
        ObjectiveFactory(company=target_company)

        # Target has only 1 export before merge
        assert Objective.objects.filter(
            company=target_company,
        ).count() == 1

        merge_companies(source_company, target_company, adviser)

        # Merge successful and target now has 2 objectives.
        assert Objective.objects.filter(
            company=target_company,
        ).count() == 2

    def test_company_eyb_lead_merges_successfully(self):
        """
        Test company merge successfully merges company `EYBLead`s.
        """
        adviser = AdviserFactory()
        source_company = CompanyFactory()
        target_company = CompanyFactory()

        EYBLeadFactory(company=source_company)
        EYBLeadFactory(company=target_company)

        # Target has only 1 export before merge
        assert EYBLead.objects.filter(
            company=target_company,
        ).count() == 1

        merge_companies(source_company, target_company, adviser)

        assert EYBLead.objects.filter(
            company=target_company,
        ).count() == 2

    def test_company_large_capital_investor_profile_merges_successfully(self):
        """
        Test company merge successfully merges company `LargeCapitalInvestorProfile`s.
        """
        adviser = AdviserFactory()
        source_company = CompanyFactory()
        target_company = CompanyFactory()

        CompleteLargeCapitalInvestorProfileFactory(investor_company=source_company)
        CompleteLargeCapitalInvestorProfileFactory(investor_company=target_company)

        # Target has only 1 export before merge
        assert LargeCapitalInvestorProfile.objects.filter(
            investor_company=target_company,
        ).count() == 1

        merge_companies(source_company, target_company, adviser)

        assert LargeCapitalInvestorProfile.objects.filter(
            investor_company=target_company,
        ).count() == 2

    def test_company_large_capital_opportunity_merges_successfully(self):
        """
        Test company merge successfully merges company `LargeCapitalOpportunity`s.
        """
        adviser = AdviserFactory()
        source_company = CompanyFactory()
        target_company = CompanyFactory()

        LargeCapitalOpportunityFactory(promoters=[source_company])
        LargeCapitalOpportunityFactory(promoters=[target_company])

        # Shared one, should not be merged.
        LargeCapitalOpportunityFactory(promoters=[target_company, source_company])

        assert LargeCapitalOpportunity.objects.filter(
            promoters=target_company,
        ).count() == 2

        merge_companies(source_company, target_company, adviser)

        assert LargeCapitalOpportunity.objects.filter(
            promoters=target_company,
        ).count() == 3

    def test_company_new_export_interaction_reminder_merges_successfully(self):
        """
        Test company merge successfully merges company `NewExportInteractionReminder`s.
        """
        adviser = AdviserFactory()
        source_company = CompanyFactory()
        target_company = CompanyFactory()

        NewExportInteractionReminderFactory(company=source_company)
        NewExportInteractionReminderFactory(company=target_company)

        # Target has only 1 export before merge
        assert NewExportInteractionReminder.objects.filter(
            company=target_company,
        ).count() == 1

        merge_companies(source_company, target_company, adviser)

        assert NewExportInteractionReminder.objects.filter(
            company=target_company,
        ).count() == 2

    def test_company_no_recent_export_interaction_reminder_merges_successfully(self):
        """
        Test company merge successfully merges company `NoRecentExportInteractionReminder`s.
        """
        adviser = AdviserFactory()
        source_company = CompanyFactory()
        target_company = CompanyFactory()

        NoRecentExportInteractionReminderFactory(company=source_company)
        NoRecentExportInteractionReminderFactory(company=target_company)

        # Target has only 1 export before merge
        assert NoRecentExportInteractionReminder.objects.filter(
            company=target_company,
        ).count() == 1

        merge_companies(source_company, target_company, adviser)

        assert NoRecentExportInteractionReminder.objects.filter(
            company=target_company,
        ).count() == 2

    def test_company_task_merges_successfully(self):
        """
        Test company merge successfully merges company `Task`s.
        """
        adviser = AdviserFactory()
        source_company = CompanyFactory()
        target_company = CompanyFactory()

        TaskFactory(company=source_company)
        TaskFactory(company=target_company)

        # Target has only 1 export before merge
        assert Task.objects.filter(
            company=target_company,
        ).count() == 1

        merge_companies(source_company, target_company, adviser)

        assert Task.objects.filter(
            company=target_company,
        ).count() == 2

    def test_company_legacy_export_wins_merges_successfully(self):
        """
        Test company merge successfully merges company `LegacyExportWinsToDataHubCompany`s.
        """
        adviser = AdviserFactory()
        source_company = CompanyFactory()
        target_company = CompanyFactory()

        LegacyExportWinsToDataHubCompanyFactory(company=source_company)
        LegacyExportWinsToDataHubCompanyFactory(company=target_company)

        # Target has only 1 export before merge
        assert LegacyExportWinsToDataHubCompany.objects.filter(
            company=target_company,
        ).count() == 1

        merge_companies(source_company, target_company, adviser)

        assert LegacyExportWinsToDataHubCompany.objects.filter(
            company=target_company,
        ).count() == 2


def _company_factory(
        num_interactions=0,
        num_contacts=0,
        num_orders=0,
        num_referrals=0,
        num_company_list_items=0,
        num_pipeline_items=0,
):
    """Factory for a company that has companies, interactions and OMIS orders."""
    company = CompanyFactory()
    ContactFactory.create_batch(num_contacts, company=company)
    CompanyInteractionFactory.create_batch(num_interactions, company=company)
    CompanyReferralFactory.create_batch(num_referrals, company=company, contact=None)
    OrderFactory.create_batch(num_orders, company=company)
    CompanyListItemFactory.create_batch(num_company_list_items, company=company)
    PipelineItemFactory.create_batch(num_pipeline_items, company=company)
    return company
