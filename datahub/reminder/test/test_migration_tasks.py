import logging

from unittest import mock

import factory

import pytest
from freezegun import freeze_time

from datahub.company.constants import OneListTierID, TeamRoleID
from datahub.company.models import Advisor
from datahub.company.test.factories import (
    AdviserFactory,
    CompanyFactory,
    OneListCoreTeamMemberFactory,
    OneListTierFactory,
)
from datahub.core.constants import InvestmentProjectStage
from datahub.feature_flag.models import UserFeatureFlagGroup
from datahub.feature_flag.test.factories import (
    UserFeatureFlagGroupFactory,
)
from datahub.investment.project.models import InvestmentProject
from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.reminder.migration_tasks import run_ita_users_migration, run_post_users_migration
from datahub.reminder.models import (
    NewExportInteractionSubscription,
    NoRecentExportInteractionSubscription,
    NoRecentInvestmentInteractionSubscription,
    UpcomingEstimatedLandDateSubscription,
)
from datahub.reminder.test.factories import (
    NewExportInteractionSubscriptionFactory,
    NoRecentExportInteractionSubscriptionFactory,
)


@pytest.mark.django_db
@freeze_time('2022-07-01T10:00:00')
class TestITAUsersMigration:
    @pytest.mark.parametrize(
        'lock_acquired',
        (False, True),
    )
    def test_lock(
        self,
        caplog,
        monkeypatch,
        lock_acquired,
    ):
        """
        Test that the task doesn't run if it cannot acquire
        the advisory_lock.
        """
        caplog.set_level(logging.INFO, logger='datahub.reminder.migration_tasks')

        monkeypatch.setattr(
            'django.conf.settings.ENABLE_AUTOMATIC_REMINDER_ITA_USER_MIGRATIONS',
            True,
        )

        UserFeatureFlagGroupFactory(code='export-notifications')

        mock_advisory_lock = mock.MagicMock()
        mock_advisory_lock.return_value.__enter__.return_value = lock_acquired
        monkeypatch.setattr(
            'datahub.reminder.migration_tasks.advisory_lock',
            mock_advisory_lock,
        )

        run_ita_users_migration()
        expected_messages = (
            [
                'Starting migration of ITA users',
                'Migrated 0 ita users',
            ]
            if lock_acquired
            else [
                'ITA users advisor list is already being processed by another worker.',
            ]
        )
        assert caplog.messages == expected_messages

    def test_no_migrations_run_when_setting_is_disabled(
        self,
        caplog,
        monkeypatch,
    ):
        """
        Test that the task runs but no users are migrated when the setting is disabled
        """
        monkeypatch.setattr(
            'django.conf.settings.ENABLE_AUTOMATIC_REMINDER_ITA_USER_MIGRATIONS',
            False,
        )
        caplog.set_level(logging.INFO, logger='datahub.reminder.migration_tasks')

        UserFeatureFlagGroupFactory(code='export-notifications')
        advisor = AdviserFactory()
        CompanyFactory(
            one_list_account_owner=advisor,
            one_list_tier_id=OneListTierID.tier_d_international_trade_advisers.value,
        )

        run_ita_users_migration()

        expected_messages = [
            'Starting migration of ITA users',
            'Automatic migration is disabled. The following 1 ita users meet the criteria for '
            'migration but will not have any changes made to their accounts.',
        ]
        assert caplog.messages[:2] == expected_messages

    def test_adviser_account_owner_of_company_in_wrong_tier_is_excluded_from_migration(
        self,
        monkeypatch,
    ):
        """
        Test when an adviser belongs to a company that is not in the Tier D -Internation Trade
        Advisors tier they are excluded from the migration
        """
        monkeypatch.setattr(
            'django.conf.settings.ENABLE_AUTOMATIC_REMINDER_ITA_USER_MIGRATIONS',
            True,
        )

        export_flag = UserFeatureFlagGroupFactory(code='export-notifications')
        advisor = AdviserFactory()
        advisor.feature_groups.set([export_flag])
        one_list_tier = OneListTierFactory()
        CompanyFactory(one_list_account_owner=advisor, one_list_tier_id=one_list_tier.id)

        run_ita_users_migration()

        assert NewExportInteractionSubscription.objects.filter(adviser=advisor).exists() is False
        assert (
            NoRecentExportInteractionSubscription.objects.filter(adviser=advisor).exists() is False
        )

    def test_adviser_account_owner_of_company_in_no_notifications_group_is_excluded(
        self,
        monkeypatch,
    ):
        """
        Test when an adviser belongs to no notification group they are excluded from the migration
        """
        monkeypatch.setattr(
            'django.conf.settings.ENABLE_AUTOMATIC_REMINDER_ITA_USER_MIGRATIONS',
            True,
        )

        no_notifications_flag = UserFeatureFlagGroupFactory(code='no-notifications')
        adviser = AdviserFactory()
        adviser.feature_groups.set([no_notifications_flag])

        CompanyFactory(
            one_list_account_owner=adviser,
            one_list_tier_id=OneListTierID.tier_d_international_trade_advisers.value,
        )

        run_ita_users_migration()

        assert NewExportInteractionSubscription.objects.filter(adviser=adviser).exists() is False
        assert (
            NoRecentExportInteractionSubscription.objects.filter(adviser=adviser).exists() is False
        )

    def test_advisor_with_feature_flag_already_is_excluded_from_migration(
        self,
        monkeypatch,
    ):
        """
        Test when an advisor already has the export-notifications feature flag they are excluded
        from the migration
        """
        monkeypatch.setattr(
            'django.conf.settings.ENABLE_AUTOMATIC_REMINDER_ITA_USER_MIGRATIONS',
            True,
        )

        export_flag = UserFeatureFlagGroupFactory(code='export-notifications')
        advisor = AdviserFactory()
        advisor.feature_groups.set([export_flag])
        CompanyFactory(
            one_list_account_owner=advisor,
            one_list_tier_id=OneListTierID.tier_d_international_trade_advisers.value,
        )
        run_ita_users_migration()

        assert NewExportInteractionSubscription.objects.filter(adviser=advisor).exists() is False
        assert (
            NoRecentExportInteractionSubscription.objects.filter(adviser=advisor).exists() is False
        )

    def test_advisor_with_subscriptions_already_get_the_feature_flag_but_do_not_get_another_subscription(  # noqa: E501
        self,
        monkeypatch,
    ):
        """
        Test when an advisor already has the export subscriptions but not the feature flag they
        are only assigned the feature flag but not any additional subscriptions
        """
        monkeypatch.setattr(
            'django.conf.settings.ENABLE_AUTOMATIC_REMINDER_ITA_USER_MIGRATIONS',
            True,
        )
        export_flag = UserFeatureFlagGroupFactory(code='export-notifications')
        advisor = AdviserFactory()
        CompanyFactory(
            one_list_account_owner=advisor,
            one_list_tier_id=OneListTierID.tier_d_international_trade_advisers.value,
        )
        NewExportInteractionSubscriptionFactory(
            adviser=advisor,
            reminder_days=[5],
            email_reminders_enabled=True,
        )

        NoRecentExportInteractionSubscriptionFactory(
            adviser=advisor,
            reminder_days=[5],
            email_reminders_enabled=True,
        )

        run_ita_users_migration()

        assert NewExportInteractionSubscription.objects.filter(adviser=advisor).count() == 1
        assert NoRecentExportInteractionSubscription.objects.filter(adviser=advisor).count() == 1
        assert Advisor.objects.filter(feature_groups=export_flag).exists() is True

    def test_new_advisor_added_to_subscription_and_assigned_feature_flag(
        self,
        monkeypatch,
    ):
        """
        Test when an advisor is the account owner for a company in the Tier D -Internation Trade
        Advisors tier and do not have the export-notifications feature flag or export
        subscriptions, they are given the export-notifications feature flag and added to the
        export subscriptions
        """
        monkeypatch.setattr(
            'django.conf.settings.ENABLE_AUTOMATIC_REMINDER_ITA_USER_MIGRATIONS',
            True,
        )

        export_flag = UserFeatureFlagGroupFactory(code='export-notifications')
        advisor = AdviserFactory()
        CompanyFactory(
            one_list_account_owner=advisor,
            one_list_tier_id=OneListTierID.tier_d_international_trade_advisers.value,
        )

        run_ita_users_migration()

        assert NewExportInteractionSubscription.objects.filter(adviser=advisor).count() == 1
        assert NoRecentExportInteractionSubscription.objects.filter(adviser=advisor).count() == 1
        assert Advisor.objects.filter(feature_groups=export_flag).exists() is True


@pytest.mark.django_db
@freeze_time('2022-07-01T10:00:00')
class TestPostUsersMigration:
    def _assert_advisor_not_migrated(
        self,
        export_flag,
        investment_flag,
        advisor,
    ):
        """
        Check the advisor does not have any subscriptions or contain any of the feature flags
        """
        self._assert_advisor_not_given_subscriptions(advisor)
        assert Advisor.objects.filter(id=advisor.id, feature_groups=export_flag).exists() is False
        assert (
            Advisor.objects.filter(id=advisor.id, feature_groups=investment_flag).exists() is False
        )

    def _assert_advisor_not_given_subscriptions(self, advisor):
        """
        Check the advisor does not have any subscriptions or contain any of the feature flags
        """
        assert NewExportInteractionSubscription.objects.filter(adviser=advisor).exists() is False
        assert (
            NoRecentExportInteractionSubscription.objects.filter(adviser=advisor).exists() is False
        )
        assert (
            NoRecentInvestmentInteractionSubscription.objects.filter(adviser=advisor).exists()
            is False
        )
        assert (
            UpcomingEstimatedLandDateSubscription.objects.filter(adviser=advisor).exists() is False
        )

    def _assert_advisor_migrated(
        self,
        export_flag,
        investment_flag,
        advisor,
    ):
        """
        Check the advisor has all the subscriptions and all feature flags
        """
        self.assert_advisor_given_subscriptions(advisor)

        assert Advisor.objects.filter(feature_groups=export_flag).exists() is True
        assert Advisor.objects.filter(feature_groups=investment_flag).exists() is True

    def assert_advisor_given_subscriptions(self, advisor):
        assert NewExportInteractionSubscription.objects.filter(adviser=advisor).exists() is True
        assert (
            NoRecentExportInteractionSubscription.objects.filter(adviser=advisor).exists() is True
        )

        assert (
            NoRecentInvestmentInteractionSubscription.objects.filter(adviser=advisor).exists()
            is True
        )

        assert (
            UpcomingEstimatedLandDateSubscription.objects.filter(adviser=advisor).exists() is True
        )

    @pytest.mark.parametrize(
        'lock_acquired',
        (False, True),
    )
    def test_lock(
        self,
        caplog,
        monkeypatch,
        lock_acquired,
    ):
        """
        Test that the task doesn't run if it cannot acquire
        the advisory_lock.
        """
        caplog.set_level(logging.INFO, logger='datahub.reminder.migration_tasks')

        monkeypatch.setattr(
            'django.conf.settings.ENABLE_AUTOMATIC_REMINDER_POST_USER_MIGRATIONS',
            True,
        )

        UserFeatureFlagGroupFactory(code='export-notifications')
        UserFeatureFlagGroupFactory(code='investment-notifications')

        mock_advisory_lock = mock.MagicMock()
        mock_advisory_lock.return_value.__enter__.return_value = lock_acquired
        monkeypatch.setattr(
            'datahub.reminder.migration_tasks.advisory_lock',
            mock_advisory_lock,
        )

        run_post_users_migration()
        expected_messages = (
            [
                'Starting migration of POST users',
                'Migrated 0 post users',
            ]
            if lock_acquired
            else [
                'Post users advisor list is already being processed by another worker.',
            ]
        )
        assert caplog.messages == expected_messages

    def test_no_migrations_run_when_setting_is_disabled(
        self,
        caplog,
        monkeypatch,
    ):
        """
        Test that the task runs but no users are migrated when the setting is disabled
        """
        monkeypatch.setattr(
            'django.conf.settings.ENABLE_AUTOMATIC_REMINDER_POST_USER_MIGRATIONS',
            False,
        )
        caplog.set_level(logging.INFO, logger='datahub.reminder.migration_tasks')

        UserFeatureFlagGroupFactory(code='export-notifications')
        UserFeatureFlagGroupFactory(code='investment-notifications')

        advisor = AdviserFactory(dit_team__role_id=TeamRoleID.post.value)
        CompanyFactory(
            one_list_account_owner=advisor,
            one_list_tier_id=OneListTierID.tier_d_overseas_post_accounts.value,
        )

        run_post_users_migration()

        assert caplog.messages[:2] == [
            'Starting migration of POST users',
            'Automatic migration is disabled. The following 1 post users meet the criteria for'
            ' migration but will not have any changes made to their accounts.',
        ]

    def test_exception_is_caught_and_logged_and_rethrown(
        self,
        caplog,
        monkeypatch,
    ):
        caplog.set_level(logging.INFO, logger='datahub.reminder.migration_tasks')
        monkeypatch.setattr(Advisor.objects, 'filter', mock.Mock(side_effect=ValueError))
        with pytest.raises(Exception):
            assert caplog.messages == [
                'Starting migration of POST users',
                'Error migrating POST users',
            ]

    def test_advisor_in_post_team_not_one_list_core_member_not_global_account_manager_no_project_link_is_excluded_from_migration(  # noqa: E501
        self,
        monkeypatch,
    ):
        """
        Test an advisor that belongs to a team that has role of POST, is not a member of the one
        list core team, is not a global account manager for a company on the Tier D - Overseas
        Post Accounts one list tier and is not linked to a project is excluded from migration
        """
        monkeypatch.setattr(
            'django.conf.settings.ENABLE_AUTOMATIC_REMINDER_POST_USER_MIGRATIONS',
            True,
        )

        export_flag = UserFeatureFlagGroupFactory(code='export-notifications')
        investment_flag = UserFeatureFlagGroupFactory(code='investment-notifications')
        advisor = AdviserFactory(dit_team__role_id=TeamRoleID.post.value)

        run_post_users_migration()

        self._assert_advisor_not_migrated(export_flag, investment_flag, advisor)

    def test_advisor_not_in_post_team_in_one_list_core_member_not_global_account_manager_no_project_link_is_excluded_from_migration(  # noqa: E501
        self,
        monkeypatch,
    ):
        """
        Test an advisor that belongs to a team that DOES NOT have a role of POST, is a member of
        the one list core team, is not a global account manager for a company on the
        Tier D - Overseas Post Accounts one list tier and is not linked to a project is
        excluded from migration
        """
        monkeypatch.setattr(
            'django.conf.settings.ENABLE_AUTOMATIC_REMINDER_POST_USER_MIGRATIONS',
            True,
        )
        export_flag = UserFeatureFlagGroupFactory(code='export-notifications')
        investment_flag = UserFeatureFlagGroupFactory(code='investment-notifications')
        advisor = AdviserFactory()

        OneListCoreTeamMemberFactory(
            adviser=advisor,
        )

        run_post_users_migration()

        self._assert_advisor_not_migrated(export_flag, investment_flag, advisor)

    def test_advisor_in_post_team_in_one_list_core_member_not_global_account_manager_no_project_link_has_both_feature_flags_is_excluded_from_migration(  # noqa: E501
        self,
        monkeypatch,
    ):
        """
        Test an advisor that belongs to a team that has a role of POST, is a member of
        the one list core team and is not a global account manager for a company on the
        Tier D - Overseas Post Accounts one list tier and is not linked to a project is
        included in the migration
        """
        monkeypatch.setattr(
            'django.conf.settings.ENABLE_AUTOMATIC_REMINDER_POST_USER_MIGRATIONS',
            True,
        )
        export_flag = UserFeatureFlagGroupFactory(code='export-notifications')
        investment_flag = UserFeatureFlagGroupFactory(code='investment-notifications')
        advisor = AdviserFactory(dit_team__role_id=TeamRoleID.post.value)
        advisor.feature_groups.set([export_flag, investment_flag])
        OneListCoreTeamMemberFactory(
            adviser=advisor,
        )

        run_post_users_migration()

        self._assert_advisor_not_given_subscriptions(advisor)

    @pytest.mark.parametrize(
        'feature_flag',
        ('export-notifications', 'investment-notifications'),
    )
    def test_advisor_in_post_team_in_one_list_core_member_not_global_account_manager_no_project_link_only_one_feature_flag_added_to_subscription_and_assigned_feature_flag(  # noqa: E501
        self,
        monkeypatch,
        feature_flag,
    ):
        """
        Test an advisor that belongs to a team that has a role of POST, is a member of the one
        list core team and is not a global account manager for a company on the Tier D - Overseas
        Post Accounts one list tier and is not linked to a project is included in the migration
        """
        monkeypatch.setattr(
            'django.conf.settings.ENABLE_AUTOMATIC_REMINDER_POST_USER_MIGRATIONS',
            True,
        )
        UserFeatureFlagGroupFactory(code='export-notifications')
        UserFeatureFlagGroupFactory(code='investment-notifications')
        advisor = AdviserFactory(dit_team__role_id=TeamRoleID.post.value)
        advisor.feature_groups.set(UserFeatureFlagGroup.objects.filter(code=feature_flag))
        OneListCoreTeamMemberFactory(
            adviser=advisor,
        )

        run_post_users_migration()

        self.assert_advisor_given_subscriptions(advisor)

    def test_advisor_not_in_post_team_in_one_list_core_member_global_account_manager_wrong_tier_company_no_project_link_is_excluded_from_migration(  # noqa: E501
        self,
        monkeypatch,
    ):
        """
        Test an advisor that belongs to a team that DOES NOT have a role of POST, is a member of
        the one list core team and is a global account manager but for a company not on the
        Tier D - Overseas Post Accounts one list tier and is not linked to a project is excluded
        from the migration
        """
        monkeypatch.setattr(
            'django.conf.settings.ENABLE_AUTOMATIC_REMINDER_POST_USER_MIGRATIONS',
            True,
        )

        export_flag = UserFeatureFlagGroupFactory(code='export-notifications')
        investment_flag = UserFeatureFlagGroupFactory(code='investment-notifications')
        advisor = AdviserFactory()
        OneListCoreTeamMemberFactory(
            adviser=advisor,
        )
        CompanyFactory(
            one_list_account_owner=advisor,
            one_list_tier_id=OneListTierID.tier_d_international_trade_advisers.value,
        )

        run_post_users_migration()

        self._assert_advisor_not_migrated(export_flag, investment_flag, advisor)

    def test_advisor_not_in_post_team_not_in_one_list_core_member_global_account_manager_correct_tier_no_project_link_is_excluded_from_migration(  # noqa: E501
        self,
        monkeypatch,
    ):
        """
        Test an advisor that belongs to a team that DOES NOT have a role of POST, is NOT a member
        of the one list core team, is a global account manager for a company on the Tier D -
        Overseas Post Accounts one list tier and is not linked to a project is included from the
        migration
        """
        monkeypatch.setattr(
            'django.conf.settings.ENABLE_AUTOMATIC_REMINDER_POST_USER_MIGRATIONS',
            True,
        )
        export_flag = UserFeatureFlagGroupFactory(code='export-notifications')
        investment_flag = UserFeatureFlagGroupFactory(code='investment-notifications')

        advisor = AdviserFactory()
        CompanyFactory(
            one_list_account_owner=advisor,
            one_list_tier_id=OneListTierID.tier_d_overseas_post_accounts.value,
        )

        run_post_users_migration()

        self._assert_advisor_not_migrated(export_flag, investment_flag, advisor)

    def test_advisor_in_post_team_not_in_one_list_core_member_global_account_manager_correct_tier_no_project_link_added_to_subscription_and_assigned_feature_flag(  # noqa: E501
        self,
        monkeypatch,
    ):
        """
        Test an advisor that belongs to a team that has a role of POST, is NOT a member
        of the one list core team, is a global account manager for a company on the Tier D -
        Overseas Post Accounts one list tier and is not linked to a project is included from the
        migration
        """
        monkeypatch.setattr(
            'django.conf.settings.ENABLE_AUTOMATIC_REMINDER_POST_USER_MIGRATIONS',
            True,
        )
        export_flag = UserFeatureFlagGroupFactory(code='export-notifications')
        investment_flag = UserFeatureFlagGroupFactory(code='investment-notifications')

        advisor = AdviserFactory(dit_team__role_id=TeamRoleID.post.value)
        CompanyFactory(
            one_list_account_owner=advisor,
            one_list_tier_id=OneListTierID.tier_d_overseas_post_accounts.value,
        )

        run_post_users_migration()

        self._assert_advisor_migrated(export_flag, investment_flag, advisor)

    @pytest.mark.parametrize(
        'status',
        (
            InvestmentProject.Status.LOST,
            InvestmentProject.Status.ABANDONED,
            InvestmentProject.Status.DORMANT,
            InvestmentProject.Status.WON,
        ),
    )
    @pytest.mark.parametrize(
        'advisor_project_role',
        (
            'project_manager',
            'project_assurance_adviser',
            'client_relationship_manager',
            'referral_source_adviser',
        ),
    )
    def test_advisor_not_in_post_team_not_in_one_list_core_member_not_global_account_manager_assigned_to_invalid_project_status_is_excluded_from_migration(  # noqa: E501
        self,
        monkeypatch,
        advisor_project_role,
        status,
    ):
        """
        Test an advisor that belongs to a team that DOES NOT have a role of POST, is NOT a member'
        ' of the one list core team and is NOT a global account manager for a company on the'
        ' Tier D - Overseas Post Accounts one list tier but is assigned to an investment project'
        ' as an {advisor_project_role} with an invalid status is excluded from the migration
        """
        monkeypatch.setattr(
            'django.conf.settings.ENABLE_AUTOMATIC_REMINDER_POST_USER_MIGRATIONS',
            True,
        )
        export_flag = UserFeatureFlagGroupFactory(code='export-notifications')
        investment_flag = UserFeatureFlagGroupFactory(code='investment-notifications')

        advisor = AdviserFactory(dit_team__role_id=TeamRoleID.post.value)
        role_field = {advisor_project_role: advisor}

        company = CompanyFactory()
        InvestmentProjectFactory(
            **role_field,
            investor_company=company,
            stage_id=InvestmentProjectStage.active.value.id,
            status=status,
        )
        self._assert_advisor_not_migrated(export_flag, investment_flag, advisor)

    @pytest.mark.parametrize(
        'status',
        (
            InvestmentProject.Status.ONGOING,
            InvestmentProject.Status.DELAYED,
        ),
    )
    @pytest.mark.parametrize(
        'advisor_project_role',
        (
            'project_manager',
            'project_assurance_adviser',
            'client_relationship_manager',
            'referral_source_adviser',
        ),
    )
    def test_advisor_in_post_team_not_in_one_list_core_member_not_global_account_manager_assigned_to_project_with_valid_status_and_stage_added_to_subscription_and_assigned_feature_flag(  # noqa: E501
        self,
        monkeypatch,
        advisor_project_role,
        status,
    ):
        """
        Test an advisor that belongs to a team that DOES NOT have a role of POST, is NOT a member'
        ' of the one list core team and is NOT a global account manager for a company on the'
        ' Tier D - Overseas Post Accounts one list tier but is assigned to an investment project'
        ' as an {advisor_project_role} with allowed stage is included in the migration
        """
        monkeypatch.setattr(
            'django.conf.settings.ENABLE_AUTOMATIC_REMINDER_POST_USER_MIGRATIONS',
            True,
        )
        export_flag = UserFeatureFlagGroupFactory(code='export-notifications')
        investment_flag = UserFeatureFlagGroupFactory(code='investment-notifications')

        advisor_to_migrate = AdviserFactory(dit_team__role_id=TeamRoleID.post.value)
        role_field = {advisor_project_role: advisor_to_migrate}
        InvestmentProjectFactory.create_batch(
            5,
            **role_field,
            investor_company=CompanyFactory(),
            stage_id=InvestmentProjectStage.active.value.id,
            status=status,
        )

        advisor_to_exclude = AdviserFactory()
        role_field = {advisor_project_role: advisor_to_exclude}

        InvestmentProjectFactory(
            **role_field,
            investor_company=CompanyFactory(),
            stage_id=InvestmentProjectStage.active.value.id,
            status=InvestmentProject.Status.ABANDONED,
        )

        run_post_users_migration()

        self._assert_advisor_migrated(export_flag, investment_flag, advisor_to_migrate)
        self._assert_advisor_not_migrated(export_flag, investment_flag, advisor_to_exclude)

    @pytest.mark.parametrize(
        'advisor_project_role',
        (
            'project_manager',
            'project_assurance_adviser',
            'client_relationship_manager',
            'referral_source_adviser',
        ),
    )
    @pytest.mark.parametrize(
        'excluded',
        (True, False),
    )
    def test_when_large_number_of_advisors_meeting_migration_criteria_are_found_all_are_migrated(
        self,
        monkeypatch,
        advisor_project_role,
        excluded,
    ):
        monkeypatch.setattr(
            'django.conf.settings.ENABLE_AUTOMATIC_REMINDER_POST_USER_MIGRATIONS',
            True,
        )
        export_flag = UserFeatureFlagGroupFactory(code='export-notifications')
        investment_flag = UserFeatureFlagGroupFactory(code='investment-notifications')

        migrated_users = []

        # Add users that don't meet any criteria
        excluded_users = AdviserFactory.create_batch(10)

        OneListCoreTeamMemberFactory.create_batch(
            len(excluded_users),
            adviser=factory.Iterator(excluded_users),
        )

        CompanyFactory.create_batch(
            len(excluded_users),
            one_list_account_owner=factory.Iterator(excluded_users),
            one_list_tier_id=OneListTierID.tier_d_international_trade_advisers.value,
        )

        InvestmentProjectFactory.create_batch(
            len(excluded_users),
            **{advisor_project_role: factory.Iterator(excluded_users)},
            investor_company=CompanyFactory(),
            stage_id=InvestmentProjectStage.active.value.id,
            status=InvestmentProject.Status.ONGOING,
        )

        # Add user in dit role and member of one list core team
        dit_role_advisors = AdviserFactory.create_batch(
            3,
            dit_team__role_id=TeamRoleID.post.value,
        )
        OneListCoreTeamMemberFactory.create_batch(
            len(dit_role_advisors),
            adviser=factory.Iterator(dit_role_advisors),
        )
        migrated_users.extend(dit_role_advisors)

        # Add user that is the account owner of a tier d company
        account_owner_advisors = AdviserFactory.create_batch(
            8,
            dit_team__role_id=TeamRoleID.post.value,
        )
        CompanyFactory.create_batch(
            len(account_owner_advisors),
            one_list_account_owner=factory.Iterator(account_owner_advisors),
            one_list_tier_id=OneListTierID.tier_d_overseas_post_accounts.value,
        )
        migrated_users.extend(account_owner_advisors)

        # Add user that has a relation to an investment project
        investment_project_advisors = AdviserFactory.create_batch(
            4,
            dit_team__role_id=TeamRoleID.post.value,
        )
        InvestmentProjectFactory.create_batch(
            len(investment_project_advisors),
            **{advisor_project_role: factory.Iterator(investment_project_advisors)},
            investor_company=CompanyFactory(),
            stage_id=InvestmentProjectStage.active.value.id,
            status=InvestmentProject.Status.ONGOING,
        )
        migrated_users.extend(investment_project_advisors)

        # Add users that meet every criteria
        all_criteria_advisors = AdviserFactory.create_batch(
            5,
            dit_team__role_id=TeamRoleID.post.value,
        )
        OneListCoreTeamMemberFactory.create_batch(
            len(all_criteria_advisors),
            adviser=factory.Iterator(all_criteria_advisors),
        )
        one_list_companies = CompanyFactory.create_batch(
            len(all_criteria_advisors),
            one_list_account_owner=factory.Iterator(all_criteria_advisors),
            one_list_tier_id=OneListTierID.tier_d_overseas_post_accounts.value,
        )
        InvestmentProjectFactory.create_batch(
            len(all_criteria_advisors),
            **{advisor_project_role: factory.Iterator(all_criteria_advisors)},
            investor_company=factory.Iterator(one_list_companies),
            stage_id=InvestmentProjectStage.active.value.id,
            status=InvestmentProject.Status.DELAYED,
        )
        migrated_users.extend(all_criteria_advisors)

        if excluded:
            no_notifications_flag = UserFeatureFlagGroupFactory(code='no-notifications')
            for adviser in migrated_users:
                adviser.feature_groups.set([no_notifications_flag])
            excluded_users += migrated_users
            migrated_users = []

        run_post_users_migration()
        for user in migrated_users:
            self._assert_advisor_migrated(export_flag, investment_flag, user)

        for user in excluded_users:
            self._assert_advisor_not_migrated(export_flag, investment_flag, user)
