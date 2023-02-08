import logging
from unittest import mock

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
from datahub.feature_flag.models import UserFeatureFlagGroup
from datahub.feature_flag.test.factories import (
    UserFeatureFlagGroupFactory,
)
from datahub.reminder.migration_tasks import migrate_ita_users, migrate_post_users
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

        UserFeatureFlagGroupFactory(code='export-notifications')

        mock_advisory_lock = mock.MagicMock()
        mock_advisory_lock.return_value.__enter__.return_value = lock_acquired
        monkeypatch.setattr(
            'datahub.reminder.migration_tasks.advisory_lock',
            mock_advisory_lock,
        )

        migrate_ita_users()
        expected_messages = (
            [
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
            'django.conf.settings.ENABLE_AUTOMATIC_REMINDER_USER_MIGRATIONS',
            False,
        )
        caplog.set_level(logging.INFO, logger='datahub.reminder.migration_tasks')

        UserFeatureFlagGroupFactory(code='export-notifications')
        advisor = AdviserFactory()
        CompanyFactory(
            one_list_account_owner=advisor,
            one_list_tier_id=OneListTierID.tier_d_international_trade_advisers.value,
        )

        migrate_ita_users()
        expected_messages = [
            'Automatic migration of users is disabled, no changes will be made to the ita user'
            f' {advisor.email} subscriptions or feature flags',
            'Migrated 1 ita users',
        ]
        assert caplog.messages == expected_messages

    def test_advisor_account_owner_of_company_in_wrong_tier_is_excluded_from_migration(
        self,
        monkeypatch,
    ):
        """
        Test when an advisor belongs to a company that is not in the Tier D -Internation Trade
        Advisors tier they are excluded from the migraton
        """
        monkeypatch.setattr(
            'django.conf.settings.ENABLE_AUTOMATIC_REMINDER_USER_MIGRATIONS',
            True,
        )

        export_flag = UserFeatureFlagGroupFactory(code='export-notifications')
        advisor = AdviserFactory()
        advisor.feature_groups.set([export_flag])
        one_list_tier = OneListTierFactory()
        CompanyFactory(one_list_account_owner=advisor, one_list_tier_id=one_list_tier.id)

        migrate_ita_users()

        assert NewExportInteractionSubscription.objects.filter(adviser=advisor).exists() is False
        assert (
            NoRecentExportInteractionSubscription.objects.filter(adviser=advisor).exists() is False
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
            'django.conf.settings.ENABLE_AUTOMATIC_REMINDER_USER_MIGRATIONS',
            True,
        )

        export_flag = UserFeatureFlagGroupFactory(code='export-notifications')
        advisor = AdviserFactory()
        advisor.feature_groups.set([export_flag])
        CompanyFactory(
            one_list_account_owner=advisor,
            one_list_tier_id=OneListTierID.tier_d_international_trade_advisers.value,
        )
        migrate_ita_users()

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
            'django.conf.settings.ENABLE_AUTOMATIC_REMINDER_USER_MIGRATIONS',
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

        migrate_ita_users()

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
            'django.conf.settings.ENABLE_AUTOMATIC_REMINDER_USER_MIGRATIONS',
            True,
        )

        export_flag = UserFeatureFlagGroupFactory(code='export-notifications')
        advisor = AdviserFactory()
        CompanyFactory(
            one_list_account_owner=advisor,
            one_list_tier_id=OneListTierID.tier_d_international_trade_advisers.value,
        )

        migrate_ita_users()

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
        assert Advisor.objects.filter(feature_groups=export_flag).exists() is False
        assert Advisor.objects.filter(feature_groups=investment_flag).exists() is False

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
        self._assert_advisor_given_subscriptions(advisor)

        assert Advisor.objects.filter(feature_groups=export_flag).exists() is True
        assert Advisor.objects.filter(feature_groups=investment_flag).exists() is True

    def _assert_advisor_given_subscriptions(self, advisor):
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

        UserFeatureFlagGroupFactory(code='export-notifications')
        UserFeatureFlagGroupFactory(code='investment-notifications')

        mock_advisory_lock = mock.MagicMock()
        mock_advisory_lock.return_value.__enter__.return_value = lock_acquired
        monkeypatch.setattr(
            'datahub.reminder.migration_tasks.advisory_lock',
            mock_advisory_lock,
        )

        migrate_post_users()
        expected_messages = (
            [
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
            'django.conf.settings.ENABLE_AUTOMATIC_REMINDER_USER_MIGRATIONS',
            False,
        )
        caplog.set_level(logging.INFO, logger='datahub.reminder.migration_tasks')

        UserFeatureFlagGroupFactory(code='export-notifications')
        UserFeatureFlagGroupFactory(code='investment-notifications')

        advisor = AdviserFactory()
        CompanyFactory(
            one_list_account_owner=advisor,
            one_list_tier_id=OneListTierID.tier_d_overseas_post_accounts.value,
        )

        migrate_post_users()
        expected_messages = [
            'Automatic migration of users is disabled, no changes will be made to the post user'
            f' {advisor.email} subscriptions or feature flags',
            'Migrated 1 post users',
        ]
        assert caplog.messages == expected_messages

    def test_advisor_in_post_team_not_one_list_core_member_not_global_account_manager_is_excluded_from_migration(  # noqa: E501
        self,
        monkeypatch,
    ):
        """
        Test an advisor that belongs to a team that has role of POST, is not a member of the one
        list core team and is not a global account manager for a company on the Tier D - Overseas
        Post Accounts one list tier is excluded from migration
        """
        monkeypatch.setattr(
            'django.conf.settings.ENABLE_AUTOMATIC_REMINDER_USER_MIGRATIONS',
            True,
        )

        export_flag = UserFeatureFlagGroupFactory(code='export-notifications')
        investment_flag = UserFeatureFlagGroupFactory(code='investment-notifications')
        advisor = AdviserFactory(dit_team__role_id=TeamRoleID.post.value)

        migrate_post_users()

        self._assert_advisor_not_migrated(export_flag, investment_flag, advisor)

    def test_advisor_not_in_post_team_in_one_list_core_member_not_global_account_manager_is_excluded_from_migration(  # noqa: E501
        self,
        monkeypatch,
    ):
        """
        Test an advisor that belongs to a team that DOES NOT have a role of POST, is a member of'
        ' the one list core team and is not a global account manager for a company on the'
        ' Tier D - Overseas Post Accounts one list tier is excluded from migration
        """
        monkeypatch.setattr(
            'django.conf.settings.ENABLE_AUTOMATIC_REMINDER_USER_MIGRATIONS',
            True,
        )
        export_flag = UserFeatureFlagGroupFactory(code='export-notifications')
        investment_flag = UserFeatureFlagGroupFactory(code='investment-notifications')
        advisor = AdviserFactory()

        OneListCoreTeamMemberFactory(
            adviser=advisor,
        )

        migrate_post_users()

        self._assert_advisor_not_migrated(export_flag, investment_flag, advisor)

    def test_advisor_in_post_team_in_one_list_core_member_not_global_account_manager_has_both_feature_flags_is_excluded_from_migration(  # noqa: E501
        self,
        monkeypatch,
    ):
        """
        Test an advisor that belongs to a team that has a role of POST, is a member of'
        ' the one list core team and is not a global account manager for a company on the'
        ' Tier D - Overseas Post Accounts one list tier is included in the migration
        """
        monkeypatch.setattr(
            'django.conf.settings.ENABLE_AUTOMATIC_REMINDER_USER_MIGRATIONS',
            True,
        )
        export_flag = UserFeatureFlagGroupFactory(code='export-notifications')
        investment_flag = UserFeatureFlagGroupFactory(code='investment-notifications')
        advisor = AdviserFactory(dit_team__role_id=TeamRoleID.post.value)
        advisor.feature_groups.set([export_flag, investment_flag])
        OneListCoreTeamMemberFactory(
            adviser=advisor,
        )

        migrate_post_users()

        self._assert_advisor_not_given_subscriptions(advisor)

    @pytest.mark.parametrize(
        'feature_flag',
        ('export-notifications', 'investment-notifications'),
    )
    def test_advisor_in_post_team_in_one_list_core_member_not_global_account_manager_only_one_feature_flag_added_to_subscription_and_assigned_feature_flag(  # noqa: E501
        self,
        monkeypatch,
        feature_flag,
    ):
        """
        Test an advisor that belongs to a team that has a role of POST, is a member of'
        ' the one list core team and is not a global account manager for a company on the'
        ' Tier D - Overseas Post Accounts one list tier is included in the migration
        """
        monkeypatch.setattr(
            'django.conf.settings.ENABLE_AUTOMATIC_REMINDER_USER_MIGRATIONS',
            True,
        )
        UserFeatureFlagGroupFactory(code='export-notifications')
        UserFeatureFlagGroupFactory(code='investment-notifications')
        advisor = AdviserFactory(dit_team__role_id=TeamRoleID.post.value)
        advisor.feature_groups.set([UserFeatureFlagGroup.objects.get(code=feature_flag)])

        OneListCoreTeamMemberFactory(
            adviser=advisor,
        )

        migrate_post_users()

        self._assert_advisor_given_subscriptions(advisor)

    def test_advisor_not_in_post_team_in_one_list_core_member_global_account_manager_wrong_tier_company_is_excluded_from_migration(  # noqa: E501
        self,
        monkeypatch,
    ):
        """
        Test an advisor that belongs to a team that DOES NOT have a role of POST, is a member of'
        ' the one list core team and is a global account manager but for a company not on the'
        ' Tier D - Overseas Post Accounts one list tier is excluded from the migration
        """
        monkeypatch.setattr(
            'django.conf.settings.ENABLE_AUTOMATIC_REMINDER_USER_MIGRATIONS',
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

        migrate_post_users()

        self._assert_advisor_not_migrated(export_flag, investment_flag, advisor)

    def test_advisor_not_in_post_team_not_in_one_list_core_member_global_account_manager_correct_tier_added_to_subscription_and_assigned_feature_flag(  # noqa: E501
        self,
        monkeypatch,
    ):
        """
        Test an advisor that belongs to a team that DOES NOT have a role of POST, is NOT a member'
        ' of the one list core team and is a global account manager for a company on the'
        ' Tier D - Overseas Post Accounts one list tier is included from the migration
        """
        monkeypatch.setattr(
            'django.conf.settings.ENABLE_AUTOMATIC_REMINDER_USER_MIGRATIONS',
            True,
        )
        export_flag = UserFeatureFlagGroupFactory(code='export-notifications')
        investment_flag = UserFeatureFlagGroupFactory(code='investment-notifications')

        advisor = AdviserFactory()
        CompanyFactory(
            one_list_account_owner=advisor,
            one_list_tier_id=OneListTierID.tier_d_overseas_post_accounts.value,
        )

        migrate_post_users()

        self._assert_advisor_migrated(export_flag, investment_flag, advisor)
