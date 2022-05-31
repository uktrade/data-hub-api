from unittest import mock
from unittest.mock import call

import pytest
from freezegun import freeze_time
from dateutil.relativedelta import relativedelta
from django.utils.timezone import now

from datahub.company.test.factories import AdviserFactory
from datahub.core.constants import InvestmentProjectStage
from datahub.feature_flag.test.factories import UserFeatureFlagFactory
from datahub.investment.project.test.factories import (
    InvestmentProjectFactory,
)
from datahub.reminder import ESTIMATED_LAND_DATE_REMINDERS_FEATURE_FLAG_NAME
from datahub.reminder.models import UpcomingEstimatedLandDateReminder
from datahub.reminder.tasks import (
    create_reminder,
    generate_estimated_land_date_reminders,
    generate_estimated_land_date_reminders_for_subscription,
)
from datahub.reminder.test.factories import (
    UpcomingEstimatedLandDateSubscriptionFactory,
)


@pytest.fixture()
def estimated_land_date_reminders_user_feature_flag():
    """
    Creates the estimated land date reminders user feature flag.
    """
    yield UserFeatureFlagFactory(
        code=ESTIMATED_LAND_DATE_REMINDERS_FEATURE_FLAG_NAME,
        is_active=True,
    )


@pytest.fixture()
def adviser(estimated_land_date_reminders_user_feature_flag):
    """
    An adviser with the relevant feature flags enabled
    """
    adviser = AdviserFactory()
    adviser.features.set([estimated_land_date_reminders_user_feature_flag])
    return adviser


@pytest.fixture()
def mock_create_reminder(monkeypatch):
    mock_create_reminder = mock.Mock()
    monkeypatch.setattr(
        'datahub.reminder.tasks.create_reminder',
        mock_create_reminder,
    )
    return mock_create_reminder


@pytest.fixture()
def mock_send_estimated_land_date_reminder(monkeypatch):
    mock_send_estimated_land_date_reminder = mock.Mock()
    monkeypatch.setattr(
        'datahub.reminder.tasks.send_estimated_land_date_reminder',
        mock_send_estimated_land_date_reminder,
    )
    return mock_send_estimated_land_date_reminder


@pytest.fixture()
def mock_generate_estimated_land_date_reminders_for_subscription(monkeypatch):
    mock_generate_estimated_land_date_reminders_for_subscription = mock.Mock()
    monkeypatch.setattr(
        'datahub.reminder.tasks.generate_estimated_land_date_reminders_for_subscription',
        mock_generate_estimated_land_date_reminders_for_subscription,
    )
    return mock_generate_estimated_land_date_reminders_for_subscription


@pytest.mark.django_db
class TestCreateReminder:
    def test_create_reminder_email(
        self,
        mock_send_estimated_land_date_reminder,
        adviser,
    ):
        """
        Create reminder should create a model instance and send an email.
        """
        days_left = 30
        future_estimated_land_date = now() + relativedelta(days=days_left)
        project = InvestmentProjectFactory(
            project_manager=adviser,
            estimated_land_date=future_estimated_land_date,
        )

        create_reminder(
            project=project,
            adviser=adviser,
            days_left=days_left,
            send_email=True,
        )
        reminders = UpcomingEstimatedLandDateReminder.objects.filter(
            adviser=adviser,
            project=project,
        )
        assert reminders.count() == 1
        assert reminders[0].event == f'{days_left} days left to estimated land date'
        mock_send_estimated_land_date_reminder.assert_called_with(
            project=project,
            adviser=adviser,
            days_left=days_left,
        )

    def test_create_reminder_no_email(
        self,
        mock_send_estimated_land_date_reminder,
        adviser,
    ):
        """
        Create reminder should create a model instance and not send an email.
        """
        days_left = 30
        future_estimated_land_date = now() + relativedelta(days=days_left)
        project = InvestmentProjectFactory(
            project_manager=adviser,
            estimated_land_date=future_estimated_land_date,
        )

        create_reminder(
            project=project,
            adviser=adviser,
            days_left=days_left,
            send_email=False,
        )
        reminders = UpcomingEstimatedLandDateReminder.objects.filter(
            adviser=adviser,
            project=project,
        )
        assert reminders.count() == 1
        assert mock_send_estimated_land_date_reminder.call_count == 0

    def test_create_existing_reminder(
        self,
        mock_send_estimated_land_date_reminder,
        adviser,
    ):
        """
        If a reminder was already made today then do not send an email.
        """
        days_left = 30
        future_estimated_land_date = now() + relativedelta(days=days_left)
        project = InvestmentProjectFactory(
            project_manager=adviser,
            estimated_land_date=future_estimated_land_date,
        )
        with freeze_time('2020-07-12T10:00:00'):
            UpcomingEstimatedLandDateReminder.objects.create(
                adviser=adviser,
                project=project,
                event=f'{days_left} days left to estimated land date',
            )

        with freeze_time('2020-07-12T19:00:00'):
            create_reminder(
                project=project,
                adviser=adviser,
                days_left=days_left,
                send_email=True,
            )
        reminders = UpcomingEstimatedLandDateReminder.objects.filter(
            adviser=adviser,
            project=project,
        )
        assert reminders.count() == 1
        assert mock_send_estimated_land_date_reminder.call_count == 0

    def test_create_another_reminder_after_estimated_land_date_change(
        self,
        mock_send_estimated_land_date_reminder,
        adviser,
    ):
        """
        If the estimated land date is changed and a reminder has already been sent out,
        a new reminder should be created and a new email sent.
        """
        days_left = 30
        future_estimated_land_date = now() + relativedelta(days=days_left)
        project = InvestmentProjectFactory(
            project_manager=adviser,
            estimated_land_date=future_estimated_land_date,
        )

        with freeze_time('2010-07-12T10:00:00'):
            UpcomingEstimatedLandDateReminder.objects.create(
                adviser=adviser,
                project=project,
                event=f'{days_left} days left to estimated land date',
            )

        create_reminder(
            project=project,
            adviser=adviser,
            days_left=days_left,
            send_email=True,
        )
        reminders = UpcomingEstimatedLandDateReminder.objects.filter(
            adviser=adviser,
            project=project,
        )
        assert reminders.count() == 2
        assert mock_send_estimated_land_date_reminder.call_count == 1


@pytest.mark.django_db
class TestGenerateEstimatedLandDateReminderTask:
    def test_generate_estimated_land_date_reminders(
        self,
        mock_generate_estimated_land_date_reminders_for_subscription,
    ):
        """
        Reminders should be generated for all subscriptions.
        """
        subscription_count = 2
        subscriptions = UpcomingEstimatedLandDateSubscriptionFactory.create_batch(
            subscription_count,
        )
        generate_estimated_land_date_reminders()
        mock_generate_estimated_land_date_reminders_for_subscription.assert_has_calls(
            [call(subscription) for subscription in subscriptions],
        )

    @pytest.mark.parametrize(
        'days,email_reminders_enabled',
        (
            (30, True),
            (60, True),
            (30, False),
            (60, False),
        ),
    )
    def test_generate_estimated_land_date_reminders_for_subscription(
        self,
        adviser,
        mock_create_reminder,
        days,
        email_reminders_enabled,
    ):
        """
        Estimated Land Date reminders should be created for relevant subscriptions.
        """
        subscription = UpcomingEstimatedLandDateSubscriptionFactory(
            adviser=adviser,
            reminder_days=[days],
            email_reminders_enabled=email_reminders_enabled,
        )
        future_estimated_land_date = now() + relativedelta(days=days)

        project = InvestmentProjectFactory(
            project_manager=adviser,
            estimated_land_date=future_estimated_land_date,
        )
        InvestmentProjectFactory(
            project_manager=adviser,
            estimated_land_date=future_estimated_land_date - relativedelta(days=120),
        )
        InvestmentProjectFactory(
            project_manager=adviser,
            estimated_land_date=future_estimated_land_date + relativedelta(days=120),
        )

        generate_estimated_land_date_reminders_for_subscription(subscription)
        mock_create_reminder.assert_called_once_with(
            project=project,
            adviser=adviser,
            days_left=days,
            send_email=email_reminders_enabled,
        )

    def test_does_not_include_verify_win_and_won_projects(self, adviser, mock_create_reminder):
        """
        A reminder should not be sent for verify win and won projects.
        """
        days = 30
        subscription = UpcomingEstimatedLandDateSubscriptionFactory(
            adviser=adviser,
            reminder_days=[days],
            email_reminders_enabled=True,
        )
        future_estimated_land_date = now() + relativedelta(days=days)

        project = InvestmentProjectFactory(
            project_manager=adviser,
            estimated_land_date=future_estimated_land_date,
        )
        InvestmentProjectFactory(
            project_manager=adviser,
            estimated_land_date=future_estimated_land_date,
            stage_id=InvestmentProjectStage.verify_win.value.id,
        )
        InvestmentProjectFactory(
            project_manager=adviser,
            estimated_land_date=future_estimated_land_date,
            stage_id=InvestmentProjectStage.won.value.id,
        )

        generate_estimated_land_date_reminders_for_subscription(subscription)
        mock_create_reminder.assert_called_once_with(
            project=project,
            adviser=adviser,
            days_left=days,
            send_email=True,
        )

    def test_no_user_feature_flag(
        self,
        mock_create_reminder,
        estimated_land_date_reminders_user_feature_flag,
    ):
        """
        Reminders should not be created if the user does not have the feature flag enabled.
        """
        days = 30
        adviser = AdviserFactory()
        subscription = UpcomingEstimatedLandDateSubscriptionFactory(
            adviser=adviser,
            reminder_days=[days],
            email_reminders_enabled=True,
        )
        future_estimated_land_date = now() + relativedelta(days=days)
        InvestmentProjectFactory(
            project_manager=adviser,
            estimated_land_date=future_estimated_land_date,
        )
        generate_estimated_land_date_reminders_for_subscription(subscription)
        assert mock_create_reminder.call_count == 0

    def test_inactive_user_feature_flag(
        self,
        mock_create_reminder,
    ):
        """
        Reminders should not be created if the user feature flag is inactive.
        """
        feature_flag = UserFeatureFlagFactory(
            code=ESTIMATED_LAND_DATE_REMINDERS_FEATURE_FLAG_NAME,
            is_active=False,
        )
        days = 30
        adviser = AdviserFactory()
        adviser.features.set([feature_flag])
        subscription = UpcomingEstimatedLandDateSubscriptionFactory(
            adviser=adviser,
            reminder_days=[days],
            email_reminders_enabled=True,
        )
        future_estimated_land_date = now() + relativedelta(days=days)
        InvestmentProjectFactory(
            project_manager=adviser,
            estimated_land_date=future_estimated_land_date,
        )
        generate_estimated_land_date_reminders_for_subscription(subscription)
        assert mock_create_reminder.call_count == 0

    def test_does_not_send_multiple(
        self,
        mock_send_estimated_land_date_reminder,
        adviser,
    ):
        """
        Only one reminder should be created.

        Even after calling the generate function multiple times, only one reminder
        should be created and one email sent.
        """
        days = 30
        future_estimated_land_date = now() + relativedelta(days=days)
        UpcomingEstimatedLandDateSubscriptionFactory(
            adviser=adviser,
            reminder_days=[days],
            email_reminders_enabled=True,
        )
        project = InvestmentProjectFactory(
            project_manager=adviser,
            estimated_land_date=future_estimated_land_date,
        )
        generate_estimated_land_date_reminders()
        generate_estimated_land_date_reminders()
        assert UpcomingEstimatedLandDateReminder.objects.filter(
            project=project,
            adviser=adviser,
        ).count() == 1
        mock_send_estimated_land_date_reminder.assert_called_once_with(
            project=project,
            adviser=adviser,
            days_left=days,
        )
