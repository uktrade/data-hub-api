import datetime
import logging
import uuid
from operator import attrgetter
from unittest import mock
from unittest.mock import ANY, call, Mock

import factory
import pytest
from dateutil.relativedelta import relativedelta
from django.utils.timezone import utc
from freezegun import freeze_time

from datahub.company.constants import OneListTierID
from datahub.company.test.factories import (
    AdviserFactory,
    CompanyFactory,
    OneListCoreTeamMemberFactory,
    OneListTierFactory,
)
from datahub.core.constants import InvestmentProjectStage
from datahub.core.queues.scheduler import LONG_RUNNING_QUEUE
from datahub.feature_flag.test.factories import (
    FeatureFlagFactory,
    UserFeatureFlagFactory,
)
from datahub.interaction.test.factories import (
    CompanyInteractionFactory,
    InvestmentProjectInteractionFactory,
)
from datahub.investment.project.models import InvestmentProject
from datahub.investment.project.test.factories import (
    ActiveInvestmentProjectFactory,
    InvestmentProjectFactory,
)
from datahub.notification.constants import NotifyServiceName
from datahub.reminder import (
    EXPORT_NEW_INTERACTION_REMINDERS_EMAIL_STATUS_FLAG_NAME,
    EXPORT_NEW_INTERACTION_REMINDERS_FEATURE_FLAG_NAME,
    EXPORT_NO_RECENT_INTERACTION_REMINDERS_EMAIL_STATUS_FLAG_NAME,
    EXPORT_NO_RECENT_INTERACTION_REMINDERS_FEATURE_FLAG_NAME,
    INVESTMENT_ESTIMATED_LAND_DATE_EMAIL_STATUS_FEATURE_FLAG_NAME,
    INVESTMENT_ESTIMATED_LAND_DATE_REMINDERS_FEATURE_FLAG_NAME,
    INVESTMENT_NO_RECENT_INTERACTION_REMINDERS_EMAIL_STATUS_FLAG_NAME,
    INVESTMENT_NO_RECENT_INTERACTION_REMINDERS_FEATURE_FLAG_NAME,
)
from datahub.reminder.models import (
    EmailDeliveryStatus,
    NewExportInteractionReminder,
    NoRecentExportInteractionReminder,
    NoRecentInvestmentInteractionReminder,
    UpcomingEstimatedLandDateReminder,
)
from datahub.reminder.tasks import (
    create_estimated_land_date_reminder,
    create_new_export_interaction_reminder,
    create_no_recent_export_interaction_reminder,
    create_no_recent_interaction_reminder,
    generate_estimated_land_date_reminders,
    generate_estimated_land_date_reminders_for_subscription,
    generate_new_export_interaction_reminders,
    generate_new_export_interaction_reminders_for_subscription,
    generate_no_recent_export_interaction_reminders,
    generate_no_recent_export_interaction_reminders_for_subscription,
    generate_no_recent_interaction_reminders,
    generate_no_recent_interaction_reminders_for_subscription,
    schedule_generate_estimated_land_date_reminders,
    update_notify_email_delivery_status_for_estimated_land_date,
    update_notify_email_delivery_status_for_new_export_interaction,
    update_notify_email_delivery_status_for_no_recent_export_interaction,
    update_notify_email_delivery_status_for_no_recent_interaction,
)
from datahub.reminder.test.factories import (
    NewExportInteractionReminderFactory,
    NewExportInteractionSubscriptionFactory,
    NoRecentExportInteractionReminderFactory,
    NoRecentExportInteractionSubscriptionFactory,
    NoRecentInvestmentInteractionReminderFactory,
    NoRecentInvestmentInteractionSubscriptionFactory,
    UpcomingEstimatedLandDateReminderFactory,
    UpcomingEstimatedLandDateSubscriptionFactory,
)


@pytest.fixture()
def no_recent_export_interaction_reminders_user_feature_flag():
    """
    Creates the no recent export interaction reminders user feature flag.
    """
    yield UserFeatureFlagFactory(
        code=EXPORT_NO_RECENT_INTERACTION_REMINDERS_FEATURE_FLAG_NAME,
        is_active=True,
    )


@pytest.fixture()
def new_export_interaction_reminders_user_feature_flag():
    """
    Creates the new export interaction reminders user feature flag.
    """
    yield UserFeatureFlagFactory(
        code=EXPORT_NEW_INTERACTION_REMINDERS_FEATURE_FLAG_NAME,
        is_active=True,
    )


@pytest.fixture()
def estimated_land_date_reminders_user_feature_flag():
    """
    Creates the estimated land date reminders user feature flag.
    """
    yield UserFeatureFlagFactory(
        code=INVESTMENT_ESTIMATED_LAND_DATE_REMINDERS_FEATURE_FLAG_NAME,
        is_active=True,
    )


@pytest.fixture()
def no_recent_interaction_reminders_user_feature_flag():
    """
    Creates the no recent interaction reminders user feature flag.
    """
    yield UserFeatureFlagFactory(
        code=INVESTMENT_NO_RECENT_INTERACTION_REMINDERS_FEATURE_FLAG_NAME,
        is_active=True,
    )


@pytest.fixture()
def adviser(
    new_export_interaction_reminders_user_feature_flag,
    no_recent_export_interaction_reminders_user_feature_flag,
    no_recent_interaction_reminders_user_feature_flag,
    estimated_land_date_reminders_user_feature_flag,
):
    """
    An adviser with the relevant feature flags enabled
    """
    adviser = AdviserFactory()
    adviser.features.set(
        [
            new_export_interaction_reminders_user_feature_flag,
            no_recent_export_interaction_reminders_user_feature_flag,
            estimated_land_date_reminders_user_feature_flag,
            no_recent_interaction_reminders_user_feature_flag,
        ],
    )
    return adviser


@pytest.fixture()
def inactive_adviser(
    new_export_interaction_reminders_user_feature_flag,
    no_recent_export_interaction_reminders_user_feature_flag,
    no_recent_interaction_reminders_user_feature_flag,
    estimated_land_date_reminders_user_feature_flag,
):
    """
    An inactive adviser with the relevant feature flags enabled
    """
    inactive_adviser = AdviserFactory(is_active=False)
    inactive_adviser.features.set(
        [
            new_export_interaction_reminders_user_feature_flag,
            no_recent_export_interaction_reminders_user_feature_flag,
            estimated_land_date_reminders_user_feature_flag,
            no_recent_interaction_reminders_user_feature_flag,
        ],
    )
    return inactive_adviser


@pytest.fixture()
def mock_create_estimated_land_date_reminder(monkeypatch):
    mock_create_estimated_land_date_reminder = mock.Mock()
    monkeypatch.setattr(
        'datahub.reminder.tasks.create_estimated_land_date_reminder',
        mock_create_estimated_land_date_reminder,
    )
    return mock_create_estimated_land_date_reminder


@pytest.fixture()
def mock_send_estimated_land_date_summary(monkeypatch):
    mock_send_estimated_land_date_summary = mock.Mock()
    monkeypatch.setattr(
        'datahub.reminder.tasks.send_estimated_land_date_summary',
        mock_send_estimated_land_date_summary,
    )
    return mock_send_estimated_land_date_summary


@pytest.fixture()
def mock_send_estimated_land_date_reminder(monkeypatch):
    mock_send_estimated_land_date_reminder = mock.Mock()
    monkeypatch.setattr(
        'datahub.reminder.tasks.send_estimated_land_date_reminder',
        mock_send_estimated_land_date_reminder,
    )
    return mock_send_estimated_land_date_reminder


@pytest.fixture()
def mock_generate_estimated_land_date_reminders(monkeypatch):
    mock_generate_estimated_land_date_reminders = mock.Mock()
    monkeypatch.setattr(
        'datahub.reminder.tasks.generate_estimated_land_date_reminders',
        mock_generate_estimated_land_date_reminders,
    )
    return mock_generate_estimated_land_date_reminders


@pytest.fixture()
def mock_schedule_generate_estimated_land_date_reminders_for_subscription(monkeypatch):
    mock_schedule_generate_estimated_land_date_reminders_for_subscription = mock.Mock()
    monkeypatch.setattr(
        'datahub.reminder.tasks.schedule_generate_estimated_land_date_reminders_for_subscription',
        mock_schedule_generate_estimated_land_date_reminders_for_subscription,
    )
    return mock_schedule_generate_estimated_land_date_reminders_for_subscription


@pytest.fixture()
def mock_create_no_recent_export_interaction_reminder(monkeypatch):
    mock_create_no_recent_export_interaction_reminder = mock.Mock()
    monkeypatch.setattr(
        'datahub.reminder.tasks.create_no_recent_export_interaction_reminder',
        mock_create_no_recent_export_interaction_reminder,
    )
    return mock_create_no_recent_export_interaction_reminder


@pytest.fixture()
def mock_send_no_recent_export_interaction_reminder(monkeypatch):
    mock_send_no_recent_export_interaction_reminder = mock.Mock()
    monkeypatch.setattr(
        'datahub.reminder.tasks.send_no_recent_export_interaction_reminder',
        mock_send_no_recent_export_interaction_reminder,
    )
    return mock_send_no_recent_export_interaction_reminder


@pytest.fixture()
def mock_generate_no_recent_export_interaction_reminders_for_subscription(monkeypatch):
    mock_generate_no_recent_export_interaction_reminders_for_subscription = mock.Mock()
    monkeypatch.setattr(
        'datahub.reminder.tasks.generate_no_recent_export_interaction_reminders_for_subscription',
        mock_generate_no_recent_export_interaction_reminders_for_subscription,
    )
    return mock_generate_no_recent_export_interaction_reminders_for_subscription


@pytest.fixture()
def mock_create_new_export_interaction_reminder(monkeypatch):
    mock_create_new_export_interaction_reminder = mock.Mock()
    monkeypatch.setattr(
        'datahub.reminder.tasks.create_new_export_interaction_reminder',
        mock_create_new_export_interaction_reminder,
    )
    return mock_create_new_export_interaction_reminder


@pytest.fixture()
def mock_send_new_export_interaction_reminder(monkeypatch):
    mock_send_new_export_interaction_reminder = mock.Mock()
    monkeypatch.setattr(
        'datahub.reminder.tasks.send_new_export_interaction_reminder',
        mock_send_new_export_interaction_reminder,
    )
    return mock_send_new_export_interaction_reminder


@pytest.fixture()
def mock_generate_new_export_interaction_reminders_for_subscription(monkeypatch):
    mock_generate_new_export_interaction_reminders_for_subscription = mock.Mock()
    monkeypatch.setattr(
        'datahub.reminder.tasks.generate_new_export_interaction_reminders_for_subscription',
        mock_generate_new_export_interaction_reminders_for_subscription,
    )
    return mock_generate_new_export_interaction_reminders_for_subscription


@pytest.fixture()
def mock_create_no_recent_interaction_reminder(monkeypatch):
    mock_create_no_recent_interaction_reminder = mock.Mock()
    monkeypatch.setattr(
        'datahub.reminder.tasks.create_no_recent_interaction_reminder',
        mock_create_no_recent_interaction_reminder,
    )
    return mock_create_no_recent_interaction_reminder


@pytest.fixture()
def mock_send_no_recent_interaction_reminder(monkeypatch):
    mock_send_no_recent_interaction_reminder = mock.Mock()
    monkeypatch.setattr(
        'datahub.reminder.tasks.send_no_recent_interaction_reminder',
        mock_send_no_recent_interaction_reminder,
    )
    return mock_send_no_recent_interaction_reminder


@pytest.fixture()
def mock_generate_no_recent_interaction_reminders_for_subscription(monkeypatch):
    mock_generate_no_recent_interaction_reminders_for_subscription = mock.Mock()
    monkeypatch.setattr(
        'datahub.reminder.tasks.generate_no_recent_interaction_reminders_for_subscription',
        mock_generate_no_recent_interaction_reminders_for_subscription,
    )
    return mock_generate_no_recent_interaction_reminders_for_subscription


@pytest.fixture()
def mock_notification_tasks_notify_gateway(monkeypatch):
    mock_notify_gateway = mock.Mock()
    monkeypatch.setattr(
        'datahub.notification.tasks.notify_gateway',
        mock_notify_gateway,
    )
    return mock_notify_gateway


@pytest.fixture()
def mock_reminder_tasks_notify_gateway(monkeypatch):
    mock_notify_gateway = mock.Mock()
    monkeypatch.setattr(
        'datahub.reminder.tasks.notify_gateway',
        mock_notify_gateway,
    )
    return mock_notify_gateway


@pytest.fixture()
def mock_job_scheduler(monkeypatch):
    mock_job_scheduler = mock.Mock()
    monkeypatch.setattr(
        'datahub.reminder.tasks.job_scheduler',
        mock_job_scheduler,
    )
    return mock_job_scheduler


@pytest.fixture()
def no_recent_export_interaction_email_status_feature_flag():
    """Creates the no recent interaction email status feature flag."""
    yield FeatureFlagFactory(
        code=EXPORT_NO_RECENT_INTERACTION_REMINDERS_EMAIL_STATUS_FLAG_NAME,
    )


@pytest.fixture()
def estimated_land_date_email_status_feature_flag():
    """Creates the estimated land date email status feature flag."""
    yield FeatureFlagFactory(code=INVESTMENT_ESTIMATED_LAND_DATE_EMAIL_STATUS_FEATURE_FLAG_NAME)


@pytest.fixture()
def no_recent_interaction_email_status_feature_flag():
    """Creates the investment no recent interaction email status feature flag."""
    yield FeatureFlagFactory(
        code=INVESTMENT_NO_RECENT_INTERACTION_REMINDERS_EMAIL_STATUS_FLAG_NAME,
    )


@pytest.fixture()
def new_export_interaction_email_status_feature_flag():
    """
    Creates the new export interaction email status feature flag.
    """
    yield FeatureFlagFactory(code=EXPORT_NEW_INTERACTION_REMINDERS_EMAIL_STATUS_FLAG_NAME)


@pytest.mark.django_db
@freeze_time('2022-07-01T10:00:00')
class TestCreateEstimatedLandDateReminder:
    current_date = datetime.date(year=2022, month=7, day=1)

    def test_create_reminder_email(
        self,
        mock_send_estimated_land_date_reminder,
        adviser,
    ):
        """
        Create reminder should create a model instance and send an email.
        """
        days_left = 30
        estimated_land_date = self.current_date + relativedelta(months=1)
        project = ActiveInvestmentProjectFactory(
            project_manager=adviser,
            estimated_land_date=estimated_land_date,
            status=InvestmentProject.Status.ONGOING,
        )

        create_estimated_land_date_reminder(
            project=project,
            adviser=adviser,
            send_email=True,
            current_date=self.current_date,
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
            reminders=[reminders[0]],
        )

    def test_create_reminder_no_email(
        self,
        mock_send_estimated_land_date_reminder,
        adviser,
    ):
        """
        Create reminder should create a model instance and not send an email.
        """
        estimated_land_date = self.current_date + relativedelta(months=1)
        project = ActiveInvestmentProjectFactory(
            project_manager=adviser,
            estimated_land_date=estimated_land_date,
            status=InvestmentProject.Status.ONGOING,
        )

        create_estimated_land_date_reminder(
            project=project,
            adviser=adviser,
            send_email=False,
            current_date=self.current_date,
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
        estimated_land_date = self.current_date + relativedelta(months=1)
        project = ActiveInvestmentProjectFactory(
            project_manager=adviser,
            estimated_land_date=estimated_land_date,
            status=InvestmentProject.Status.ONGOING,
        )
        with freeze_time('2022-07-01T10:00:00'):
            UpcomingEstimatedLandDateReminder.objects.create(
                adviser=adviser,
                project=project,
                event=f'{days_left} days left to estimated land date',
            )

        with freeze_time('2022-07-01T16:00:00'):
            create_estimated_land_date_reminder(
                project=project,
                adviser=adviser,
                send_email=True,
                current_date=self.current_date,
            )
        reminders = UpcomingEstimatedLandDateReminder.objects.filter(
            adviser=adviser,
            project=project,
        )
        assert reminders.count() == 1
        assert mock_send_estimated_land_date_reminder.call_count == 0

    def test_create_existing_reminder_slow_queue(
        self,
        mock_send_estimated_land_date_reminder,
        adviser,
    ):
        """
        If the queue is still processing tasks from yesterday and a reminder
        was already sent, do not send another one.
        """
        days_left = 30
        estimated_land_date = self.current_date + relativedelta(months=1)
        project = ActiveInvestmentProjectFactory(
            project_manager=adviser,
            estimated_land_date=estimated_land_date,
            status=InvestmentProject.Status.ONGOING,
        )
        with freeze_time('2022-07-01T10:00:00'):
            UpcomingEstimatedLandDateReminder.objects.create(
                adviser=adviser,
                project=project,
                event=f'{days_left} days left to estimated land date',
            )

        with freeze_time('2022-07-02T10:00:00'):
            create_estimated_land_date_reminder(
                project=project,
                adviser=adviser,
                send_email=True,
                current_date=self.current_date,
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
        estimated_land_date = self.current_date + relativedelta(months=1)
        project = ActiveInvestmentProjectFactory(
            project_manager=adviser,
            estimated_land_date=estimated_land_date,
            status=InvestmentProject.Status.ONGOING,
        )

        with freeze_time('2010-07-01T10:00:00'):
            UpcomingEstimatedLandDateReminder.objects.create(
                adviser=adviser,
                project=project,
                event=f'{days_left} days left to estimated land date',
            )

        create_estimated_land_date_reminder(
            project=project,
            adviser=adviser,
            send_email=True,
            current_date=self.current_date,
        )
        reminders = UpcomingEstimatedLandDateReminder.objects.filter(
            adviser=adviser,
            project=project,
        )
        assert reminders.count() == 2
        assert mock_send_estimated_land_date_reminder.call_count == 1


@pytest.mark.django_db
@freeze_time('2022-07-01T10:00:00')
class TestGenerateEstimatedLandDateReminderTask:
    current_date = datetime.date(year=2022, month=7, day=1)

    def test_schedule_generate_estimated_land_date_reminders(
        self,
        caplog,
        mock_job_scheduler,
    ):
        """
        Generate estimated land date reminders should be called from
        scheduler.
        """
        caplog.set_level(logging.INFO)

        job = schedule_generate_estimated_land_date_reminders()
        mock_job_scheduler.assert_called_once()

        # check result
        assert caplog.messages[0] == (
            f'Task {job.id} generate_estimated_land_date_reminders scheduled'
        )

    def test_generate_estimated_land_date_reminders(
        self,
        mock_schedule_generate_estimated_land_date_reminders_for_subscription,
    ):
        """
        Reminders should be generated for all subscriptions.
        """
        subscription_count = 2
        subscriptions = UpcomingEstimatedLandDateSubscriptionFactory.create_batch(
            subscription_count,
        )
        generate_estimated_land_date_reminders()
        mock_schedule_generate_estimated_land_date_reminders_for_subscription.assert_has_calls(
            [
                call(subscription=subscription, current_date=self.current_date)
                for subscription in subscriptions
            ],
            any_order=True,
        )

    @pytest.mark.parametrize(
        'role',
        (
            'project_manager',
            'project_assurance_adviser',
            'client_relationship_manager',
            'referral_source_adviser',
        ),
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
        mock_create_estimated_land_date_reminder,
        days,
        email_reminders_enabled,
        role,
    ):
        """
        Estimated Land Date reminders should be created for relevant subscriptions.
        """
        subscription = UpcomingEstimatedLandDateSubscriptionFactory(
            adviser=adviser,
            reminder_days=[days],
            email_reminders_enabled=email_reminders_enabled,
        )
        estimated_land_date = self.current_date + relativedelta(
            months=days // 30,
        )

        role_field = {role: adviser}
        project = ActiveInvestmentProjectFactory(
            **role_field,
            estimated_land_date=estimated_land_date,
            status=InvestmentProject.Status.ONGOING,
        )
        ActiveInvestmentProjectFactory(
            **role_field,
            estimated_land_date=estimated_land_date - relativedelta(months=3),
            status=InvestmentProject.Status.ONGOING,
        )
        ActiveInvestmentProjectFactory(
            **role_field,
            estimated_land_date=estimated_land_date + relativedelta(months=3),
            status=InvestmentProject.Status.ONGOING,
        )

        generate_estimated_land_date_reminders_for_subscription(
            subscription=subscription,
            current_date=self.current_date,
        )
        mock_create_estimated_land_date_reminder.assert_called_once_with(
            project=project,
            adviser=adviser,
            send_email=email_reminders_enabled,
            current_date=self.current_date,
        )

    @pytest.mark.parametrize(
        'role',
        (
            'project_manager',
            'project_assurance_adviser',
            'client_relationship_manager',
            'referral_source_adviser',
        ),
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
    def test_sends_estimated_land_date_summary_notification_for_subscription(
        self,
        adviser,
        mock_create_estimated_land_date_reminder,
        mock_send_estimated_land_date_summary,
        days,
        email_reminders_enabled,
        role,
    ):
        """
        Estimated Land Date summary notification should be sent when number of reminders reaches a
        threshold.
        """
        subscription = UpcomingEstimatedLandDateSubscriptionFactory(
            adviser=adviser,
            reminder_days=[days],
            email_reminders_enabled=email_reminders_enabled,
        )
        estimated_land_date = self.current_date + relativedelta(
            months=days // 30,
        )

        role_field = {role: adviser}
        projects = ActiveInvestmentProjectFactory.create_batch(
            6,
            **role_field,
            estimated_land_date=estimated_land_date,
            status=InvestmentProject.Status.ONGOING,
        )

        generate_estimated_land_date_reminders_for_subscription(
            subscription=subscription,
            current_date=self.current_date,
        )
        projects.sort(key=attrgetter('pk'))

        if email_reminders_enabled:
            mock_send_estimated_land_date_summary.assert_called_once_with(
                projects=projects,
                adviser=adviser,
                current_date=self.current_date,
                reminders=ANY,
            )
        else:
            mock_send_estimated_land_date_summary.assert_not_called()

        mock_create_estimated_land_date_reminder.assert_has_calls(
            [
                call(
                    project=project,
                    adviser=adviser,
                    send_email=False,
                    current_date=self.current_date,
                )
                for project in projects
            ],
            any_order=True,
        )

    def test_active_ongoing_or_delayed_projects_only(
        self,
        adviser,
        mock_create_estimated_land_date_reminder,
    ):
        """
        A reminder should only be sent for active ongoing or active delayed projects.
        """
        days = 30
        subscription = UpcomingEstimatedLandDateSubscriptionFactory(
            adviser=adviser,
            reminder_days=[days],
            email_reminders_enabled=True,
        )
        estimated_land_date = self.current_date + relativedelta(months=1)

        active_ongoing_project = ActiveInvestmentProjectFactory(
            project_manager=adviser,
            estimated_land_date=estimated_land_date,
            status=InvestmentProject.Status.ONGOING,
        )
        active_delayed_project = ActiveInvestmentProjectFactory(
            project_manager=adviser,
            estimated_land_date=estimated_land_date,
            status=InvestmentProject.Status.DELAYED,
        )
        InvestmentProjectFactory(
            project_manager=adviser,
            estimated_land_date=estimated_land_date,
            stage_id=InvestmentProjectStage.verify_win.value.id,
            status=InvestmentProject.Status.ONGOING,
        )
        InvestmentProjectFactory(
            project_manager=adviser,
            estimated_land_date=estimated_land_date,
            stage_id=InvestmentProjectStage.won.value.id,
            status=InvestmentProject.Status.ONGOING,
        )
        ActiveInvestmentProjectFactory(
            project_manager=adviser,
            estimated_land_date=estimated_land_date,
            status=InvestmentProject.Status.ABANDONED,
        )

        generate_estimated_land_date_reminders_for_subscription(
            subscription=subscription,
            current_date=self.current_date,
        )
        mock_create_estimated_land_date_reminder.assert_has_calls(
            [
                call(
                    project=project,
                    adviser=adviser,
                    send_email=True,
                    current_date=self.current_date,
                )
                for project in [active_ongoing_project, active_delayed_project]
            ],
            any_order=True,
        )

    def test_wont_send_notifications_if_no_projects(
        self,
        adviser,
        mock_create_estimated_land_date_reminder,
    ):
        """
        A reminder should not be sent if adviser has no projects.
        """
        days = 30
        subscription = UpcomingEstimatedLandDateSubscriptionFactory(
            adviser=adviser,
            reminder_days=[days],
            email_reminders_enabled=True,
        )
        generate_estimated_land_date_reminders_for_subscription(
            subscription=subscription,
            current_date=self.current_date,
        )
        mock_create_estimated_land_date_reminder.assert_not_called()

    def test_no_user_feature_flag(
        self,
        mock_create_estimated_land_date_reminder,
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
        estimated_land_date = self.current_date + relativedelta(months=1)
        ActiveInvestmentProjectFactory(
            project_manager=adviser,
            estimated_land_date=estimated_land_date,
            status=InvestmentProject.Status.ONGOING,
        )
        generate_estimated_land_date_reminders_for_subscription(
            subscription=subscription,
            current_date=self.current_date,
        )
        assert mock_create_estimated_land_date_reminder.call_count == 0

    def test_inactive_user_feature_flag(
        self,
        mock_create_estimated_land_date_reminder,
    ):
        """
        Reminders should not be created if the user feature flag is inactive.
        """
        feature_flag = UserFeatureFlagFactory(
            code=INVESTMENT_ESTIMATED_LAND_DATE_REMINDERS_FEATURE_FLAG_NAME,
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
        estimated_land_date = self.current_date + relativedelta(months=1)
        ActiveInvestmentProjectFactory(
            project_manager=adviser,
            estimated_land_date=estimated_land_date,
            status=InvestmentProject.Status.ONGOING,
        )
        generate_estimated_land_date_reminders_for_subscription(
            subscription=subscription,
            current_date=self.current_date,
        )
        assert mock_create_estimated_land_date_reminder.call_count == 0

    def test_inactive_user(
        self,
        inactive_adviser,
        mock_create_estimated_land_date_reminder,
    ):
        """
        Reminders should not be created if the user is inactive.
        """
        days = 30
        UpcomingEstimatedLandDateSubscriptionFactory(
            adviser=inactive_adviser,
            reminder_days=[days],
            email_reminders_enabled=True,
        )
        estimated_land_date = self.current_date + relativedelta(months=1)
        ActiveInvestmentProjectFactory(
            project_manager=inactive_adviser,
            estimated_land_date=estimated_land_date,
            status=InvestmentProject.Status.ONGOING,
        )
        generate_estimated_land_date_reminders()
        assert mock_create_estimated_land_date_reminder.call_count == 0

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
        estimated_land_date = self.current_date + relativedelta(months=1)
        UpcomingEstimatedLandDateSubscriptionFactory(
            adviser=adviser,
            reminder_days=[days],
            email_reminders_enabled=True,
        )
        project = ActiveInvestmentProjectFactory(
            project_manager=adviser,
            estimated_land_date=estimated_land_date,
            status=InvestmentProject.Status.ONGOING,
        )
        generate_estimated_land_date_reminders()
        generate_estimated_land_date_reminders()
        assert (
            UpcomingEstimatedLandDateReminder.objects.filter(
                project=project,
                adviser=adviser,
            ).count()
            == 1
        )
        reminder = UpcomingEstimatedLandDateReminder.objects.get(project=project, adviser=adviser)
        mock_send_estimated_land_date_reminder.assert_called_once_with(
            project=project,
            adviser=adviser,
            days_left=days,
            reminders=[reminder],
        )

    def test_stores_notification_id(
        self,
        async_queue,
        caplog,
        mock_reminder_tasks_notify_gateway,
        adviser,
    ):
        """
        Test if a notification id is being stored against the reminder.
        """
        caplog.set_level(logging.INFO, logger='datahub.reminder.tasks')
        notification_id = uuid.uuid4()
        mock_reminder_tasks_notify_gateway.send_email_notification = mock.Mock(
            return_value={'id': notification_id},
        )

        days = 30
        estimated_land_date = self.current_date + relativedelta(months=1)
        UpcomingEstimatedLandDateSubscriptionFactory(
            adviser=adviser,
            reminder_days=[days],
            email_reminders_enabled=True,
        )
        project = ActiveInvestmentProjectFactory(
            project_manager=adviser,
            estimated_land_date=estimated_land_date,
            status=InvestmentProject.Status.ONGOING,
        )
        generate_estimated_land_date_reminders()

        reminder = UpcomingEstimatedLandDateReminder.objects.get(project=project, adviser=adviser)
        assert reminder.email_notification_id == notification_id
        assert reminder.email_delivery_status == EmailDeliveryStatus.UNKNOWN

    def test_stores_notification_id_for_summary_email(
        self,
        async_queue,
        mock_reminder_tasks_notify_gateway,
        adviser,
    ):
        """
        Test if a notification id is being stored against the reminders from summary email.
        """
        notification_id = uuid.uuid4()
        mock_reminder_tasks_notify_gateway.send_email_notification = mock.Mock(
            return_value={'id': notification_id},
        )

        days = 30
        estimated_land_date = self.current_date + relativedelta(months=1)
        UpcomingEstimatedLandDateSubscriptionFactory(
            adviser=adviser,
            reminder_days=[days],
            email_reminders_enabled=True,
        )
        projects = ActiveInvestmentProjectFactory.create_batch(
            6,
            project_manager=adviser,
            estimated_land_date=estimated_land_date,
            status=InvestmentProject.Status.ONGOING,
        )
        generate_estimated_land_date_reminders()

        reminders = UpcomingEstimatedLandDateReminder.objects.filter(
            project__in=projects,
            adviser=adviser,
        )
        assert all(reminder.email_notification_id == notification_id for reminder in reminders)
        assert all(
            reminder.email_delivery_status == EmailDeliveryStatus.UNKNOWN for reminder in reminders
        )

    def test_does_not_send_multiple_summary(
        self,
        async_queue,
        mock_send_estimated_land_date_summary,
        adviser,
    ):
        """
        Even after calling the generate function multiple times, only one summary email
        should be sent.
        """
        days = 30
        estimated_land_date = self.current_date + relativedelta(months=1)
        UpcomingEstimatedLandDateSubscriptionFactory(
            adviser=adviser,
            reminder_days=[days],
            email_reminders_enabled=True,
        )
        projects = ActiveInvestmentProjectFactory.create_batch(
            6,
            project_manager=adviser,
            estimated_land_date=estimated_land_date,
            status=InvestmentProject.Status.ONGOING,
        )
        projects.sort(key=attrgetter('pk'))
        generate_estimated_land_date_reminders()
        generate_estimated_land_date_reminders()
        reminders = UpcomingEstimatedLandDateReminder.objects.filter(
            project__in=(project.pk for project in projects),
            adviser=adviser,
        )
        assert reminders.count() == 6
        mock_send_estimated_land_date_summary.assert_called_once_with(
            projects=projects,
            adviser=adviser,
            current_date=self.current_date,
            reminders=list(reminders),
        )


@pytest.mark.django_db
@freeze_time('2022-11-22T10:00:00')
class TestCreateNoRecentExportInteractionReminder:
    current_date = datetime.date(year=2022, month=11, day=22)

    def test_create_reminder_email(
        self,
        mock_send_no_recent_export_interaction_reminder,
        adviser,
    ):
        """
        Create reminder should create a model instance and send an email.
        """
        reminder_days = 5
        company = OneListCoreTeamMemberFactory(
            adviser=adviser,
        ).company
        interaction = CompanyInteractionFactory(company=company)

        create_no_recent_export_interaction_reminder(
            company=company,
            adviser=adviser,
            interaction=interaction,
            reminder_days=reminder_days,
            send_email=True,
            current_date=self.current_date,
        )
        reminders = NoRecentExportInteractionReminder.objects.filter(
            adviser=adviser,
        )
        expected_event = f'No recent interaction with {company.name} in {reminder_days}\xa0days'
        assert reminders.count() == 1
        assert reminders[0].event == expected_event
        mock_send_no_recent_export_interaction_reminder.assert_called_with(
            company=company,
            interaction=interaction,
            adviser=adviser,
            reminder_days=reminder_days,
            current_date=self.current_date,
            reminders=[reminders[0]],
        )

    def test_create_reminder_no_email(
        self,
        mock_send_no_recent_export_interaction_reminder,
        adviser,
    ):
        """Create reminder should create a model instance and not send an email."""
        reminder_days = 5
        company = OneListCoreTeamMemberFactory(
            adviser=adviser,
        ).company
        interaction = CompanyInteractionFactory(company=company)

        create_no_recent_export_interaction_reminder(
            company=company,
            adviser=adviser,
            interaction=interaction,
            reminder_days=reminder_days,
            send_email=False,
            current_date=self.current_date,
        )
        reminders = NoRecentExportInteractionReminder.objects.filter(adviser=adviser)
        assert reminders.count() == 1
        assert mock_send_no_recent_export_interaction_reminder.call_count == 0

    def test_create_existing_reminder(
        self,
        mock_send_no_recent_export_interaction_reminder,
        adviser,
    ):
        """
        If a reminder was already made today then do not send an email.
        """
        reminder_days = 5
        company = OneListCoreTeamMemberFactory(
            adviser=adviser,
        ).company
        interaction = CompanyInteractionFactory(company=company)
        event = f'No recent interaction with {company.name} in {reminder_days}\xa0days'
        with freeze_time('2022-11-22T10:00:00'):
            NoRecentExportInteractionReminder.objects.create(
                adviser=adviser,
                company=company,
                interaction=interaction,
                event=event,
            )
        with freeze_time('2022-11-22T16:00:00'):
            create_no_recent_export_interaction_reminder(
                company=company,
                adviser=adviser,
                interaction=interaction,
                reminder_days=reminder_days,
                send_email=True,
                current_date=self.current_date,
            )
        reminders = NoRecentExportInteractionReminder.objects.filter(
            adviser=adviser,
            company=company,
            interaction=interaction,
        )
        assert reminders.count() == 1
        assert mock_send_no_recent_export_interaction_reminder.call_count == 0

    def test_create_existing_reminder_slow_queue(
        self,
        mock_send_no_recent_export_interaction_reminder,
        adviser,
    ):
        """
        If the queue is still processing tasks from yesterday and a reminder
        was already sent, do not send another one.
        """
        reminder_days = 5
        company = OneListCoreTeamMemberFactory(
            adviser=adviser,
        ).company
        interaction = CompanyInteractionFactory(company=company)
        event = f'No recent interaction with {company.name} in {reminder_days}\xa0days'
        with freeze_time('2022-11-22T10:00:00'):
            NoRecentExportInteractionReminder.objects.create(
                adviser=adviser,
                company=company,
                interaction=interaction,
                event=event,
            )

        with freeze_time('2022-11-23T16:00:00'):
            create_no_recent_export_interaction_reminder(
                company=company,
                adviser=adviser,
                interaction=interaction,
                reminder_days=reminder_days,
                send_email=True,
                current_date=self.current_date,
            )
        reminders = NoRecentExportInteractionReminder.objects.filter(
            adviser=adviser,
            company=company,
            interaction=interaction,
        )
        assert reminders.count() == 1
        assert mock_send_no_recent_export_interaction_reminder.call_count == 0


@pytest.mark.django_db
@freeze_time('2022-11-22T10:00:00')
class TestGenerateNoRecentExportInteractionReminderTask:
    current_date = datetime.date(year=2022, month=11, day=22)

    @pytest.mark.parametrize(
        'lock_acquired',
        (False, True),
    )
    def test_lock(
        self,
        caplog,
        monkeypatch,
        lock_acquired,
        mock_job_scheduler,
    ):
        """
        Test that the task doesn't run if it cannot acquire
        the advisory_lock.
        """
        caplog.set_level(logging.INFO, logger='datahub.reminder.tasks')

        mock_job_scheduler.return_value = Mock(id=1234)

        NoRecentExportInteractionSubscriptionFactory()

        mock_advisory_lock = mock.MagicMock()
        mock_advisory_lock.return_value.__enter__.return_value = lock_acquired
        monkeypatch.setattr(
            'datahub.reminder.tasks.advisory_lock',
            mock_advisory_lock,
        )

        generate_no_recent_export_interaction_reminders()
        expected_messages = (
            [
                'Task 1234 generate_no_recent_export_interaction_reminders_for_subscription',
            ]
            if lock_acquired
            else [
                'Reminders for no recent export interactions are already being processed by'
                ' another worker.',
            ]
        )
        assert caplog.messages == expected_messages

        if lock_acquired:
            mock_job_scheduler.assert_called_once()
        else:
            mock_job_scheduler.assert_not_called()

    def test_generate_no_recent_export_interaction_reminders(
        self,
        mock_job_scheduler,
    ):
        """
        Reminders should be generated for all subscriptions.
        """
        subscription_count = 2
        subscriptions = NoRecentExportInteractionSubscriptionFactory.create_batch(
            subscription_count,
        )
        generate_no_recent_export_interaction_reminders()
        mock_job_scheduler.assert_has_calls(
            [
                call(
                    queue_name=LONG_RUNNING_QUEUE,
                    function=generate_no_recent_export_interaction_reminders_for_subscription,
                    function_kwargs={
                        'subscription': subscription,
                        'current_date': self.current_date,
                    },
                    max_retries=5,
                    retry_backoff=True,
                    retry_intervals=30,
                )
                for subscription in subscriptions
            ],
            any_order=True,
        )

    @pytest.mark.parametrize(
        'days,email_reminders_enabled, one_list_tier',
        (
            (5, True, OneListTierID.tier_d_international_trade_advisers.value),
            (10, True, OneListTierID.tier_d_overseas_post_accounts.value),
            (3, False, OneListTierID.tier_d_international_trade_advisers.value),
            (15, False, OneListTierID.tier_d_overseas_post_accounts.value),
        ),
    )
    def test_generate_no_recent_export_interaction_reminders_for_subscription(
        self,
        adviser,
        mock_create_no_recent_export_interaction_reminder,
        days,
        email_reminders_enabled,
        one_list_tier,
    ):
        """
        No Recent Export Interaction reminders should be created for relevant subscriptions.
        """
        subscription = NoRecentExportInteractionSubscriptionFactory(
            adviser=adviser,
            reminder_days=[days],
            email_reminders_enabled=email_reminders_enabled,
        )

        company = CompanyFactory(
            one_list_account_owner=adviser,
            one_list_tier_id=one_list_tier,
        )

        interaction_date = self.current_date - relativedelta(days=days)

        with freeze_time(interaction_date):
            interaction = CompanyInteractionFactory(
                company=company,
            )

        generate_no_recent_export_interaction_reminders_for_subscription(
            subscription=subscription,
            current_date=self.current_date,
        )
        mock_create_no_recent_export_interaction_reminder.assert_called_once_with(
            company=company,
            adviser=adviser,
            interaction=interaction,
            reminder_days=days,
            send_email=email_reminders_enabled,
            current_date=self.current_date,
        )

    @pytest.mark.parametrize(
        'one_list_tier',
        (
            (OneListTierID.tier_d_international_trade_advisers.value),
            (OneListTierID.tier_d_overseas_post_accounts.value),
        ),
    )
    def test_generate_no_recent_export_interaction_reminders_for_subscription_for_core_member(
        self,
        adviser,
        mock_create_no_recent_export_interaction_reminder,
        one_list_tier,
    ):
        """
        No Recent Export Interaction reminders should be created for relevant subscriptions.
        """
        subscription = NoRecentExportInteractionSubscriptionFactory(
            adviser=adviser,
            reminder_days=[5],
            email_reminders_enabled=True,
        )

        company = OneListCoreTeamMemberFactory(
            adviser=adviser,
            company=CompanyFactory(
                one_list_tier_id=one_list_tier,
            ),
        ).company

        interaction_date = self.current_date - relativedelta(days=5)

        with freeze_time(interaction_date):
            interaction = CompanyInteractionFactory(
                company=company,
            )

        generate_no_recent_export_interaction_reminders_for_subscription(
            subscription=subscription,
            current_date=self.current_date,
        )
        mock_create_no_recent_export_interaction_reminder.assert_called_once_with(
            company=company,
            adviser=adviser,
            interaction=interaction,
            reminder_days=5,
            send_email=True,
            current_date=self.current_date,
        )

    def test_dont_generate_reminder_for_company_in_invalid_one_company_tier_and_no_core_team_members(  # noqa: E501
        self,
        adviser,
        mock_create_no_recent_export_interaction_reminder,
    ):
        """
        No Recent Export Interaction reminders should be created for relevant subscriptions.
        """
        subscription = NoRecentExportInteractionSubscriptionFactory(
            adviser=adviser,
            reminder_days=[5],
            email_reminders_enabled=True,
        )

        one_list_tier = OneListTierFactory()

        company = CompanyFactory(one_list_account_owner=adviser, one_list_tier_id=one_list_tier.id)

        interaction_date = self.current_date - relativedelta(days=5)

        with freeze_time(interaction_date):
            CompanyInteractionFactory(company=company)

        generate_no_recent_export_interaction_reminders_for_subscription(
            subscription=subscription,
            current_date=self.current_date,
        )
        mock_create_no_recent_export_interaction_reminder.assert_not_called()

    def test_send_reminder_if_no_interactions_at_all_in_given_timeframe(
        self,
        adviser,
        mock_create_no_recent_export_interaction_reminder,
    ):
        """
        A reminder should be sent if no interactions at all in given timeframe
        """
        day = 15
        subscription = NoRecentExportInteractionSubscriptionFactory(
            adviser=adviser,
            reminder_days=[day],
            email_reminders_enabled=True,
        )
        interaction_date = self.current_date - relativedelta(days=day)

        with freeze_time(interaction_date):
            company = CompanyFactory(
                one_list_account_owner=adviser,
                one_list_tier_id=OneListTierID.tier_d_international_trade_advisers.value,
            )

        generate_no_recent_export_interaction_reminders_for_subscription(
            subscription=subscription,
            current_date=self.current_date,
        )
        mock_create_no_recent_export_interaction_reminder.assert_called_once_with(
            company=company,
            adviser=adviser,
            interaction=None,
            reminder_days=day,
            send_email=True,
            current_date=self.current_date,
        )
        mock_create_no_recent_export_interaction_reminder.reset_mock()
        next_day = self.current_date + relativedelta(days=1)
        generate_no_recent_export_interaction_reminders_for_subscription(
            subscription=subscription,
            current_date=next_day,
        )
        mock_create_no_recent_export_interaction_reminder.assert_not_called()

    @pytest.mark.parametrize('day_offset', (0, 1))
    def test_dont_send_reminder_if_recent_interaction_exists(
        self,
        adviser,
        mock_create_no_recent_export_interaction_reminder,
        day_offset,
    ):
        """
        A reminder should only be sent if there is no recent interaction.
        """
        day = 15
        subscription = NoRecentExportInteractionSubscriptionFactory(
            adviser=adviser,
            reminder_days=[day],
            email_reminders_enabled=True,
        )
        interaction_date = self.current_date - relativedelta(days=day)

        company = CompanyFactory(
            one_list_account_owner=adviser,
            one_list_tier_id=OneListTierID.tier_d_international_trade_advisers.value,
        )

        with freeze_time(interaction_date + relativedelta(days=day_offset)):
            CompanyInteractionFactory(company=company)
        recent_interaction_date = self.current_date - relativedelta(days=5)
        with freeze_time(recent_interaction_date):
            CompanyInteractionFactory(company=company)

        generate_no_recent_interaction_reminders_for_subscription(
            subscription=subscription,
            current_date=self.current_date,
        )
        mock_create_no_recent_export_interaction_reminder.assert_not_called()

    def test_no_user_feature_flag(
        self,
        mock_create_no_recent_export_interaction_reminder,
    ):
        """
        Reminders should not be created if the user does not have the feature flag enabled.
        """
        days = 15
        adviser = AdviserFactory()
        subscription = NoRecentExportInteractionSubscriptionFactory(
            adviser=adviser,
            reminder_days=[days],
            email_reminders_enabled=True,
        )

        company = CompanyFactory(
            one_list_account_owner=adviser,
            one_list_tier_id=OneListTierID.tier_d_international_trade_advisers.value,
        )

        interaction_date = self.current_date - relativedelta(days=days)
        with freeze_time(interaction_date):
            CompanyInteractionFactory(company=company)

        generate_no_recent_export_interaction_reminders_for_subscription(
            subscription=subscription,
            current_date=self.current_date,
        )
        assert mock_create_no_recent_export_interaction_reminder.call_count == 0

    def test_inactive_user_feature_flag(
        self,
        mock_create_no_recent_export_interaction_reminder,
    ):
        """
        Reminders should not be created if the user feature flag is inactive.
        """
        feature_flag = UserFeatureFlagFactory(
            code=EXPORT_NO_RECENT_INTERACTION_REMINDERS_FEATURE_FLAG_NAME,
            is_active=False,
        )
        days = 15
        adviser = AdviserFactory()
        adviser.features.set([feature_flag])
        subscription = NoRecentExportInteractionSubscriptionFactory(
            adviser=adviser,
            reminder_days=[days],
            email_reminders_enabled=True,
        )
        company = CompanyFactory(
            one_list_account_owner=adviser,
            one_list_tier_id=OneListTierID.tier_d_international_trade_advisers.value,
        )
        interaction_date = self.current_date - relativedelta(days=days)
        with freeze_time(interaction_date):
            CompanyInteractionFactory(company=company)

        generate_no_recent_export_interaction_reminders_for_subscription(
            subscription=subscription,
            current_date=self.current_date,
        )
        assert mock_create_no_recent_export_interaction_reminder.call_count == 0

    def test_inactive_user(
        self,
        mock_create_no_recent_export_interaction_reminder,
        inactive_adviser,
    ):
        """
        Reminders should not be created if the user is inactive.
        """
        days = 15
        NoRecentExportInteractionSubscriptionFactory(
            adviser=inactive_adviser,
            reminder_days=[days],
            email_reminders_enabled=True,
        )
        company = CompanyFactory(
            one_list_account_owner=inactive_adviser,
            one_list_tier_id=OneListTierID.tier_d_international_trade_advisers.value,
        )
        interaction_date = self.current_date - relativedelta(days=days)
        with freeze_time(interaction_date):
            CompanyInteractionFactory(company=company)

        generate_no_recent_export_interaction_reminders()
        assert mock_create_no_recent_export_interaction_reminder.call_count == 0

    def test_stores_notification_id(
        self,
        mock_reminder_tasks_notify_gateway,
        adviser,
    ):
        """
        Test if a notification id is being stored against the reminder.
        """
        notification_id = uuid.uuid4()
        mock_reminder_tasks_notify_gateway.send_email_notification = mock.Mock(
            return_value={'id': notification_id},
        )

        days = 5

        subscription = NoRecentExportInteractionSubscriptionFactory(
            adviser=adviser,
            reminder_days=[days],
            email_reminders_enabled=True,
        )

        company = CompanyFactory(
            one_list_account_owner=adviser,
            one_list_tier_id=OneListTierID.tier_d_international_trade_advisers.value,
        )

        interaction_date = self.current_date - relativedelta(days=days)

        with freeze_time(interaction_date):
            interaction = CompanyInteractionFactory(
                company=company,
            )

        generate_no_recent_export_interaction_reminders_for_subscription(
            subscription=subscription,
            current_date=self.current_date,
        )

        reminder = NoRecentExportInteractionReminder.objects.get(
            interaction=interaction,
            adviser=adviser,
        )
        assert reminder.email_notification_id == notification_id
        assert reminder.email_delivery_status == EmailDeliveryStatus.UNKNOWN


@pytest.mark.django_db
@freeze_time('2022-11-22T10:00:00')
class TestCreateNewExportInteractionReminder:
    current_date = datetime.date(year=2022, month=11, day=22)

    def test_create_reminder_email(
        self,
        mock_send_new_export_interaction_reminder,
        adviser,
    ):
        """
        Create reminder should create a model instance and send an email.
        """
        reminder_days = 5
        company = OneListCoreTeamMemberFactory(
            adviser=adviser,
        ).company
        interaction = CompanyInteractionFactory(company=company)

        create_new_export_interaction_reminder(
            company=company,
            adviser=adviser,
            interaction=interaction,
            reminder_days=reminder_days,
            send_email=True,
            current_date=self.current_date,
        )
        reminders = NewExportInteractionReminder.objects.filter(
            adviser=adviser,
        )
        expected_event = f'New interaction with {company.name}'
        assert reminders.count() == 1
        assert reminders[0].event == expected_event
        mock_send_new_export_interaction_reminder.assert_called_with(
            company=company,
            interaction=interaction,
            adviser=adviser,
            reminder_days=reminder_days,
            current_date=self.current_date,
            reminders=[reminders[0]],
        )

    def test_create_reminder_no_email(
        self,
        mock_send_new_export_interaction_reminder,
        adviser,
    ):
        """Create reminder should create a model instance and not send an email."""
        reminder_days = 5
        company = OneListCoreTeamMemberFactory(
            adviser=adviser,
        ).company
        interaction = CompanyInteractionFactory(company=company)

        create_new_export_interaction_reminder(
            company=company,
            adviser=adviser,
            interaction=interaction,
            reminder_days=reminder_days,
            send_email=False,
            current_date=self.current_date,
        )
        reminders = NewExportInteractionReminder.objects.filter(adviser=adviser)
        assert reminders.count() == 1
        assert mock_send_new_export_interaction_reminder.call_count == 0

    @pytest.mark.parametrize(
        'when',
        (
            '2022-11-22T16:00:00',
            # If the queue is still processing tasks from yesterday and a reminder
            # was already sent, do not send another one.
            '2022-11-23T16:00:00',
        ),
    )
    def test_create_existing_reminder(
        self,
        mock_send_new_export_interaction_reminder,
        adviser,
        when,
    ):
        """
        If a reminder was already sent then do not send one again.
        """
        reminder_days = 5
        company = OneListCoreTeamMemberFactory(
            adviser=adviser,
        ).company
        interaction = CompanyInteractionFactory(company=company)
        event = f'New interaction with {company.name}'
        with freeze_time('2022-11-22T10:00:00'):
            NewExportInteractionReminder.objects.create(
                adviser=adviser,
                company=company,
                interaction=interaction,
                event=event,
            )
        with freeze_time(when):
            create_new_export_interaction_reminder(
                company=company,
                adviser=adviser,
                interaction=interaction,
                reminder_days=reminder_days,
                send_email=True,
                current_date=self.current_date,
            )
        reminders = NewExportInteractionReminder.objects.filter(
            adviser=adviser,
            company=company,
            interaction=interaction,
        )
        assert reminders.count() == 1
        assert mock_send_new_export_interaction_reminder.call_count == 0


@pytest.mark.django_db
@freeze_time('2022-11-22T10:00:00')
class TestGenerateNewExportInteractionReminderTask:
    current_date = datetime.date(year=2022, month=11, day=22)

    @pytest.mark.parametrize(
        'lock_acquired',
        (False, True),
    )
    def test_lock(
        self,
        caplog,
        monkeypatch,
        lock_acquired,
        mock_job_scheduler,
    ):
        """
        Test that the task doesn't run if it cannot acquire
        the advisory_lock.
        """
        caplog.set_level(logging.INFO, logger='datahub.reminder.tasks')

        mock_job_scheduler.return_value = Mock(id=1234)

        NewExportInteractionSubscriptionFactory()

        mock_advisory_lock = mock.MagicMock()
        mock_advisory_lock.return_value.__enter__.return_value = lock_acquired
        monkeypatch.setattr(
            'datahub.reminder.tasks.advisory_lock',
            mock_advisory_lock,
        )

        generate_new_export_interaction_reminders()
        expected_messages = (
            [
                'Task 1234 generate_new_export_interaction_reminders_for_subscription',
            ]
            if lock_acquired
            else [
                'Reminders for new export interactions are already being processed by another '
                'worker.',
            ]
        )
        assert caplog.messages == expected_messages

        if lock_acquired:
            mock_job_scheduler.assert_called_once()
        else:
            mock_job_scheduler.assert_not_called()

    def test_generate_new_export_interaction_reminders(
        self,
        mock_job_scheduler,
    ):
        """
        Reminders should be generated for all subscriptions.
        """
        subscription_count = 2
        subscriptions = NewExportInteractionSubscriptionFactory.create_batch(
            subscription_count,
        )
        generate_new_export_interaction_reminders()
        mock_job_scheduler.assert_has_calls(
            [
                call(
                    queue_name=LONG_RUNNING_QUEUE,
                    function=generate_new_export_interaction_reminders_for_subscription,
                    function_kwargs={
                        'subscription': subscription,
                        'current_date': self.current_date,
                    },
                    max_retries=5,
                    retry_backoff=True,
                    retry_intervals=30,
                )
                for subscription in subscriptions
            ],
            any_order=True,
        )

    @pytest.mark.parametrize(
        'days,email_reminders_enabled',
        (
            (5, True),
            (10, True),
            (3, False),
            (15, False),
        ),
    )
    def test_generate_new_export_interaction_reminders_for_subscription(
        self,
        adviser,
        mock_create_new_export_interaction_reminder,
        days,
        email_reminders_enabled,
    ):
        """
        New Export Interaction reminders should be created for relevant subscriptions.
        """
        subscription = NewExportInteractionSubscriptionFactory(
            adviser=adviser,
            reminder_days=[days],
            email_reminders_enabled=email_reminders_enabled,
        )

        company = CompanyFactory(
            one_list_account_owner=adviser,
            one_list_tier_id=OneListTierID.tier_d_international_trade_advisers.value,
        )

        interaction_date = self.current_date - relativedelta(days=days)

        with freeze_time(interaction_date):
            interaction = CompanyInteractionFactory(
                company=company,
            )

        generate_new_export_interaction_reminders_for_subscription(
            subscription=subscription,
            current_date=self.current_date,
        )
        mock_create_new_export_interaction_reminder.assert_called_once_with(
            company=company,
            adviser=adviser,
            interaction=interaction,
            reminder_days=days,
            send_email=email_reminders_enabled,
            current_date=self.current_date,
        )

    def test_dont_send_reminder_when_advisor_did_not_create_the_interaction(
        self,
        new_export_interaction_reminders_user_feature_flag,
        mock_create_new_export_interaction_reminder,
    ):
        """
        New Export Interaction reminders should not be sent to the advisor who created the
        interaction, they should only go to an advisor when they did not create the interaction
        """

        def _export_interaction_advisor(day):
            advisor = AdviserFactory()
            advisor.features.set(
                [
                    new_export_interaction_reminders_user_feature_flag,
                ],
            )

            subscription = NewExportInteractionSubscriptionFactory(
                adviser=advisor,
                reminder_days=[day],
                email_reminders_enabled=True,
            )
            company = CompanyFactory(
                one_list_account_owner=advisor,
                one_list_tier_id=OneListTierID.tier_d_international_trade_advisers.value,
            )

            return advisor, company, subscription

        day = 15
        interaction_date = self.current_date - relativedelta(days=day)

        # setup 3 advisors, along with a company and subscription - 1 advisor with only company
        # interactions they created, 1 with a mix of company interactions they created and created
        # by another advisor, and 1 with only company interactions created by another advisor
        (
            only_own_interactions_advisor,
            only_own_interactions_company,
            only_own_interactions_subscription,
        ) = _export_interaction_advisor(day)
        with freeze_time(interaction_date):
            CompanyInteractionFactory.create_batch(
                3,
                company=only_own_interactions_company,
                created_by=only_own_interactions_advisor,
            )

        (
            own_and_other_interations_advisor,
            own_and_other_interations_company,
            own_and_other_interations_subscription,
        ) = _export_interaction_advisor(day)
        with freeze_time(interaction_date):
            CompanyInteractionFactory.create_batch(
                3,
                company=own_and_other_interations_company,
                created_by=own_and_other_interations_advisor,
            )
            own_and_other_interations_expected_interaction = CompanyInteractionFactory(
                company=own_and_other_interations_company,
            )

        (
            only_other_interactions_advisor,
            only_other_interactions_company,
            only_other_interactions_subscription,
        ) = _export_interaction_advisor(day)
        with freeze_time(interaction_date):
            only_other_interactions_expected_interaction = CompanyInteractionFactory(
                company=only_other_interactions_company,
            )

        generate_new_export_interaction_reminders_for_subscription(
            subscription=only_own_interactions_subscription,
            current_date=self.current_date,
        )
        generate_new_export_interaction_reminders_for_subscription(
            subscription=own_and_other_interations_subscription,
            current_date=self.current_date,
        )
        generate_new_export_interaction_reminders_for_subscription(
            subscription=only_other_interactions_subscription,
            current_date=self.current_date,
        )

        assert mock_create_new_export_interaction_reminder.call_count == 2
        mock_create_new_export_interaction_reminder.assert_has_calls(
            [
                mock.call(
                    company=own_and_other_interations_company,
                    adviser=own_and_other_interations_advisor,
                    interaction=own_and_other_interations_expected_interaction,
                    reminder_days=day,
                    send_email=True,
                    current_date=self.current_date,
                ),
                mock.call(
                    company=only_other_interactions_company,
                    adviser=only_other_interactions_advisor,
                    interaction=only_other_interactions_expected_interaction,
                    reminder_days=day,
                    send_email=True,
                    current_date=self.current_date,
                ),
            ],
        )

    def test_dont_send_reminder_when_advisor_modifed_the_interaction(
        self,
        new_export_interaction_reminders_user_feature_flag,
        mock_create_new_export_interaction_reminder,
    ):
        """
        New Export Interaction reminders should not be sent to the advisor who modified the
        interaction
        """
        creator_advisor = AdviserFactory()
        creator_advisor.features.set(
            [
                new_export_interaction_reminders_user_feature_flag,
            ],
        )

        modifier_advisor = AdviserFactory()
        modifier_advisor.features.set(
            [
                new_export_interaction_reminders_user_feature_flag,
            ],
        )

        subscription = NewExportInteractionSubscriptionFactory(
            adviser=modifier_advisor,
            reminder_days=[15],
            email_reminders_enabled=True,
        )

        company = CompanyFactory(
            one_list_account_owner=modifier_advisor,
            one_list_tier_id=OneListTierID.tier_d_international_trade_advisers.value,
        )

        interaction_date = self.current_date - relativedelta(days=15)
        with freeze_time(interaction_date):
            interaction = CompanyInteractionFactory(
                company=company,
                created_by=creator_advisor,
            )

        interaction.notes = 'Test modification'
        interaction.modified_by = modifier_advisor
        interaction.save()

        generate_new_export_interaction_reminders_for_subscription(
            subscription=subscription,
            current_date=self.current_date,
        )

        assert mock_create_new_export_interaction_reminder.call_count == 0

    @pytest.mark.parametrize('day_offset', (0, 1))
    def test_dont_send_reminder_if_no_new_interactions(
        self,
        adviser,
        mock_create_no_recent_export_interaction_reminder,
        day_offset,
    ):
        """
        A reminder should only be sent if there is an interaction on set date.
        """
        day = 15
        subscription = NewExportInteractionSubscriptionFactory(
            adviser=adviser,
            reminder_days=[day],
            email_reminders_enabled=True,
        )
        interaction_date = self.current_date - relativedelta(days=day)

        company = CompanyFactory(
            one_list_account_owner=adviser,
            one_list_tier_id=OneListTierID.tier_d_international_trade_advisers.value,
        )

        with freeze_time(interaction_date + relativedelta(days=1)):
            CompanyInteractionFactory(company=company)
        with freeze_time(interaction_date - relativedelta(days=1)):
            CompanyInteractionFactory(company=company)

        generate_no_recent_interaction_reminders_for_subscription(
            subscription=subscription,
            current_date=self.current_date,
        )
        mock_create_no_recent_export_interaction_reminder.assert_not_called()

    def test_no_user_feature_flag(
        self,
        mock_create_new_export_interaction_reminder,
    ):
        """
        Reminders should not be created if the user does not have the feature flag enabled.
        """
        days = 15
        adviser = AdviserFactory()
        subscription = NewExportInteractionSubscriptionFactory(
            adviser=adviser,
            reminder_days=[days],
            email_reminders_enabled=True,
        )

        company = CompanyFactory(
            one_list_account_owner=adviser,
            one_list_tier_id=OneListTierID.tier_d_international_trade_advisers.value,
        )

        interaction_date = self.current_date - relativedelta(days=days)
        with freeze_time(interaction_date):
            CompanyInteractionFactory(company=company)

        generate_new_export_interaction_reminders_for_subscription(
            subscription=subscription,
            current_date=self.current_date,
        )
        assert mock_create_new_export_interaction_reminder.call_count == 0

    def test_inactive_user_feature_flag(
        self,
        mock_create_new_export_interaction_reminder,
    ):
        """
        Reminders should not be created if the user feature flag is inactive.
        """
        feature_flag = UserFeatureFlagFactory(
            code=EXPORT_NEW_INTERACTION_REMINDERS_FEATURE_FLAG_NAME,
            is_active=False,
        )
        days = 15
        adviser = AdviserFactory()
        adviser.features.set([feature_flag])
        subscription = NewExportInteractionSubscriptionFactory(
            adviser=adviser,
            reminder_days=[days],
            email_reminders_enabled=True,
        )
        company = CompanyFactory(
            one_list_account_owner=adviser,
            one_list_tier_id=OneListTierID.tier_d_international_trade_advisers.value,
        )
        interaction_date = self.current_date - relativedelta(days=days)
        with freeze_time(interaction_date):
            CompanyInteractionFactory(company=company)

        generate_new_export_interaction_reminders_for_subscription(
            subscription=subscription,
            current_date=self.current_date,
        )
        assert mock_create_new_export_interaction_reminder.call_count == 0

    def test_inactive_user(
        self,
        mock_create_new_export_interaction_reminder,
        inactive_adviser,
    ):
        """
        Reminders should not be created if the user is inactive.
        """
        days = 15
        NewExportInteractionSubscriptionFactory(
            adviser=inactive_adviser,
            reminder_days=[days],
            email_reminders_enabled=True,
        )
        company = CompanyFactory(
            one_list_account_owner=inactive_adviser,
            one_list_tier_id=OneListTierID.tier_d_international_trade_advisers.value,
        )
        interaction_date = self.current_date - relativedelta(days=days)
        with freeze_time(interaction_date):
            CompanyInteractionFactory(company=company)

        generate_new_export_interaction_reminders()
        assert mock_create_new_export_interaction_reminder.call_count == 0

    def test_stores_notification_id(
        self,
        mock_reminder_tasks_notify_gateway,
        adviser,
    ):
        """
        Test if a notification id is being stored against the reminder.
        """
        notification_id = uuid.uuid4()
        mock_reminder_tasks_notify_gateway.send_email_notification = mock.Mock(
            return_value={'id': notification_id},
        )

        days = 5

        subscription = NewExportInteractionSubscriptionFactory(
            adviser=adviser,
            reminder_days=[days],
            email_reminders_enabled=True,
        )

        company = CompanyFactory(
            one_list_account_owner=adviser,
            one_list_tier_id=OneListTierID.tier_d_international_trade_advisers.value,
        )

        interaction_date = self.current_date - relativedelta(days=days)

        with freeze_time(interaction_date):
            interaction = CompanyInteractionFactory(
                company=company,
            )

        generate_new_export_interaction_reminders_for_subscription(
            subscription=subscription,
            current_date=self.current_date,
        )

        reminder = NewExportInteractionReminder.objects.get(
            interaction=interaction,
            adviser=adviser,
        )
        assert reminder.email_notification_id == notification_id
        assert reminder.email_delivery_status == EmailDeliveryStatus.UNKNOWN


@pytest.mark.django_db
@freeze_time('2022-07-17T10:00:00')
class TestCreateNoRecentInteractionReminder:
    current_date = datetime.date(year=2022, month=7, day=17)

    def test_create_reminder_email(
        self,
        mock_send_no_recent_interaction_reminder,
        adviser,
    ):
        """
        Create reminder should create a model instance and send an email.
        """
        reminder_days = 5
        project = ActiveInvestmentProjectFactory(
            project_manager=adviser,
            status=InvestmentProject.Status.ONGOING,
        )

        create_no_recent_interaction_reminder(
            project=project,
            adviser=adviser,
            reminder_days=reminder_days,
            send_email=True,
            current_date=self.current_date,
        )
        reminders = NoRecentInvestmentInteractionReminder.objects.filter(
            adviser=adviser,
            project=project,
        )
        expected_event = f'No recent interaction with {project.name} in {reminder_days}\xa0days'
        assert reminders.count() == 1
        assert reminders[0].event == expected_event
        mock_send_no_recent_interaction_reminder.assert_called_with(
            project=project,
            adviser=adviser,
            reminder_days=reminder_days,
            current_date=self.current_date,
            reminders=[reminders[0]],
        )

    def test_create_reminder_no_email(
        self,
        mock_send_no_recent_interaction_reminder,
        adviser,
    ):
        """
        Create reminder should create a model instance and not send an email.
        """
        reminder_days = 5
        project = ActiveInvestmentProjectFactory(
            project_manager=adviser,
            status=InvestmentProject.Status.ONGOING,
        )

        create_no_recent_interaction_reminder(
            project=project,
            adviser=adviser,
            reminder_days=reminder_days,
            send_email=False,
            current_date=self.current_date,
        )
        reminders = NoRecentInvestmentInteractionReminder.objects.filter(
            adviser=adviser,
            project=project,
        )
        assert reminders.count() == 1
        assert mock_send_no_recent_interaction_reminder.call_count == 0

    def test_create_existing_reminder(
        self,
        mock_send_no_recent_interaction_reminder,
        adviser,
    ):
        """
        If a reminder was already made today then do not send an email.
        """
        reminder_days = 5
        project = ActiveInvestmentProjectFactory(
            project_manager=adviser,
            status=InvestmentProject.Status.ONGOING,
        )
        event = f'No recent interaction with {project.name} in {reminder_days}\xa0days'
        with freeze_time('2022-07-17T10:00:00'):
            NoRecentInvestmentInteractionReminder.objects.create(
                adviser=adviser,
                project=project,
                event=event,
            )

        with freeze_time('2022-07-17T16:00:00'):
            create_no_recent_interaction_reminder(
                project=project,
                adviser=adviser,
                reminder_days=reminder_days,
                send_email=True,
                current_date=self.current_date,
            )
        reminders = NoRecentInvestmentInteractionReminder.objects.filter(
            adviser=adviser,
            project=project,
        )
        assert reminders.count() == 1
        assert mock_send_no_recent_interaction_reminder.call_count == 0

    def test_create_existing_reminder_slow_queue(
        self,
        mock_send_no_recent_interaction_reminder,
        adviser,
    ):
        """
        If the queue is still processing tasks from yesterday and a reminder
        was already sent, do not send another one.
        """
        reminder_days = 5
        project = ActiveInvestmentProjectFactory(
            project_manager=adviser,
            status=InvestmentProject.Status.ONGOING,
        )
        event = f'No recent interaction with {project.name} in {reminder_days}\xa0days'
        with freeze_time('2022-07-17T10:00:00'):
            NoRecentInvestmentInteractionReminder.objects.create(
                adviser=adviser,
                project=project,
                event=event,
            )

        with freeze_time('2022-07-18T10:00:00'):
            create_no_recent_interaction_reminder(
                project=project,
                adviser=adviser,
                reminder_days=reminder_days,
                send_email=True,
                current_date=self.current_date,
            )
        reminders = NoRecentInvestmentInteractionReminder.objects.filter(
            adviser=adviser,
            project=project,
        )
        assert reminders.count() == 1
        assert mock_send_no_recent_interaction_reminder.call_count == 0


@pytest.mark.django_db
@freeze_time('2022-07-17T10:00:00')
class TestGenerateNoRecentInteractionReminderTask:
    current_date = datetime.date(year=2022, month=7, day=17)

    def test_generate_no_recent_interaction_reminders(
        self,
        mock_job_scheduler,
    ):
        """
        Reminders should be generated for all subscriptions.
        """
        subscription_count = 2
        subscriptions = NoRecentInvestmentInteractionSubscriptionFactory.create_batch(
            subscription_count,
        )
        generate_no_recent_interaction_reminders()

        mock_job_scheduler.assert_called()

        mock_job_scheduler.assert_has_calls(
            [
                call(
                    function=generate_no_recent_interaction_reminders_for_subscription,
                    function_args=(
                        subscription,
                        datetime.date(2022, 7, 17),
                    ),
                    max_retries=5,
                    queue_name=LONG_RUNNING_QUEUE,
                    retry_backoff=True,
                    retry_intervals=30,
                )
                for subscription in subscriptions
            ],
            any_order=True,
        )

    @pytest.mark.parametrize(
        'role',
        (
            'project_manager',
            'project_assurance_adviser',
            'client_relationship_manager',
            'referral_source_adviser',
        ),
    )
    @pytest.mark.parametrize(
        'days,email_reminders_enabled',
        (
            (5, True),
            (10, True),
            (3, False),
            (15, False),
        ),
    )
    def test_generate_no_recent_interaction_reminders_for_subscription(
        self,
        adviser,
        mock_create_no_recent_interaction_reminder,
        days,
        email_reminders_enabled,
        role,
    ):
        """
        No Recent Interaction reminders should be created for relevant subscriptions.
        """
        subscription = NoRecentInvestmentInteractionSubscriptionFactory(
            adviser=adviser,
            reminder_days=[days],
            email_reminders_enabled=email_reminders_enabled,
        )
        interaction_date = self.current_date - relativedelta(days=days)

        role_field = {role: adviser}
        project = ActiveInvestmentProjectFactory(
            **role_field,
            status=InvestmentProject.Status.ONGOING,
        )
        with freeze_time(interaction_date):
            InvestmentProjectInteractionFactory(investment_project=project)

        generate_no_recent_interaction_reminders_for_subscription(
            subscription=subscription,
            current_date=self.current_date,
        )
        mock_create_no_recent_interaction_reminder.assert_called_once_with(
            project=project,
            adviser=adviser,
            reminder_days=days,
            send_email=email_reminders_enabled,
            current_date=self.current_date,
        )

    def test_active_ongoing_or_delayed_projects_only(
        self,
        adviser,
        mock_create_no_recent_interaction_reminder,
    ):
        """
        A reminder should only be sent for active ongoing or active delayed projects.
        """
        day = 15
        subscription = NoRecentInvestmentInteractionSubscriptionFactory(
            adviser=adviser,
            reminder_days=[day],
            email_reminders_enabled=True,
        )
        interaction_date = self.current_date - relativedelta(days=day)

        active_ongoing_project = ActiveInvestmentProjectFactory(
            project_manager=adviser,
            status=InvestmentProject.Status.ONGOING,
        )
        active_delayed_project = ActiveInvestmentProjectFactory(
            project_manager=adviser,
            status=InvestmentProject.Status.DELAYED,
        )

        verify_win_ongoing_project = InvestmentProjectFactory(
            project_manager=adviser,
            stage_id=InvestmentProjectStage.verify_win.value.id,
            status=InvestmentProject.Status.ONGOING,
        )
        won_ongoing_project = InvestmentProjectFactory(
            project_manager=adviser,
            stage_id=InvestmentProjectStage.won.value.id,
            status=InvestmentProject.Status.ONGOING,
        )
        abandoned_project = ActiveInvestmentProjectFactory(
            project_manager=adviser,
            status=InvestmentProject.Status.ABANDONED,
        )
        with freeze_time(interaction_date):
            projects = [
                active_ongoing_project,
                active_delayed_project,
                verify_win_ongoing_project,
                won_ongoing_project,
                abandoned_project,
            ]
            InvestmentProjectInteractionFactory.create_batch(
                len(projects),
                investment_project=factory.Iterator(projects),
            )

        generate_no_recent_interaction_reminders_for_subscription(
            subscription=subscription,
            current_date=self.current_date,
        )
        mock_create_no_recent_interaction_reminder.assert_has_calls(
            [
                call(
                    project=project,
                    adviser=adviser,
                    reminder_days=day,
                    send_email=True,
                    current_date=self.current_date,
                )
                for project in [active_ongoing_project, active_delayed_project]
            ],
            any_order=True,
        )

    def test_send_reminder_if_no_interactions_at_all_in_given_timeframe(
        self,
        adviser,
        mock_create_no_recent_interaction_reminder,
    ):
        """
        A reminder should be sent if no interactions at all in given timeframe
        """
        day = 15
        subscription = NoRecentInvestmentInteractionSubscriptionFactory(
            adviser=adviser,
            reminder_days=[day],
            email_reminders_enabled=True,
        )
        interaction_date = self.current_date - relativedelta(days=day)

        with freeze_time(interaction_date):
            project = ActiveInvestmentProjectFactory(
                project_manager=adviser,
                status=InvestmentProject.Status.ONGOING,
            )

        generate_no_recent_interaction_reminders_for_subscription(
            subscription=subscription,
            current_date=self.current_date,
        )
        mock_create_no_recent_interaction_reminder.assert_called_once_with(
            project=project,
            adviser=adviser,
            reminder_days=day,
            send_email=True,
            current_date=self.current_date,
        )
        mock_create_no_recent_interaction_reminder.reset_mock()
        next_day = self.current_date + relativedelta(days=1)
        generate_no_recent_interaction_reminders_for_subscription(
            subscription=subscription,
            current_date=next_day,
        )
        mock_create_no_recent_interaction_reminder.assert_not_called()

    @pytest.mark.parametrize('day_offset', (0, 1))
    def test_dont_send_reminder_if_recent_interaction_exists(
        self,
        adviser,
        mock_create_no_recent_interaction_reminder,
        day_offset,
    ):
        """
        A reminder should only be sent if there is no recent interaction.
        """
        day = 15
        subscription = NoRecentInvestmentInteractionSubscriptionFactory(
            adviser=adviser,
            reminder_days=[day],
            email_reminders_enabled=True,
        )
        interaction_date = self.current_date - relativedelta(days=day)

        project = ActiveInvestmentProjectFactory(
            project_manager=adviser,
            status=InvestmentProject.Status.ONGOING,
        )

        with freeze_time(interaction_date + relativedelta(days=day_offset)):
            InvestmentProjectInteractionFactory(investment_project=project)

        recent_interaction_date = self.current_date - relativedelta(days=5)
        with freeze_time(recent_interaction_date):
            InvestmentProjectInteractionFactory(investment_project=project)

        generate_no_recent_interaction_reminders_for_subscription(
            subscription=subscription,
            current_date=self.current_date,
        )
        mock_create_no_recent_interaction_reminder.assert_not_called()

    def test_no_user_feature_flag(
        self,
        mock_create_no_recent_interaction_reminder,
        no_recent_interaction_reminders_user_feature_flag,
    ):
        """
        Reminders should not be created if the user does not have the feature flag enabled.
        """
        days = 15
        adviser = AdviserFactory()
        subscription = NoRecentInvestmentInteractionSubscriptionFactory(
            adviser=adviser,
            reminder_days=[days],
            email_reminders_enabled=True,
        )

        project = ActiveInvestmentProjectFactory(
            project_manager=adviser,
            status=InvestmentProject.Status.ONGOING,
        )
        interaction_date = self.current_date - relativedelta(days=days)
        with freeze_time(interaction_date):
            InvestmentProjectInteractionFactory(investment_project=project)

        generate_no_recent_interaction_reminders_for_subscription(
            subscription=subscription,
            current_date=self.current_date,
        )
        assert mock_create_no_recent_interaction_reminder.call_count == 0

    def test_inactive_user_feature_flag(
        self,
        mock_create_no_recent_interaction_reminder,
    ):
        """
        Reminders should not be created if the user feature flag is inactive.
        """
        feature_flag = UserFeatureFlagFactory(
            code=INVESTMENT_NO_RECENT_INTERACTION_REMINDERS_FEATURE_FLAG_NAME,
            is_active=False,
        )
        days = 15
        adviser = AdviserFactory()
        adviser.features.set([feature_flag])
        subscription = NoRecentInvestmentInteractionSubscriptionFactory(
            adviser=adviser,
            reminder_days=[days],
            email_reminders_enabled=True,
        )
        project = ActiveInvestmentProjectFactory(
            project_manager=adviser,
            status=InvestmentProject.Status.ONGOING,
        )
        interaction_date = self.current_date - relativedelta(days=days)
        with freeze_time(interaction_date):
            InvestmentProjectInteractionFactory(investment_project=project)

        generate_no_recent_interaction_reminders_for_subscription(
            subscription=subscription,
            current_date=self.current_date,
        )
        assert mock_create_no_recent_interaction_reminder.call_count == 0

    def test_inactive_user(
        self,
        mock_create_no_recent_interaction_reminder,
        inactive_adviser,
    ):
        """
        Reminders should not be created if the user is inactive.
        """
        days = 15
        NoRecentInvestmentInteractionSubscriptionFactory(
            adviser=inactive_adviser,
            reminder_days=[days],
            email_reminders_enabled=True,
        )
        project = ActiveInvestmentProjectFactory(
            project_manager=inactive_adviser,
            status=InvestmentProject.Status.ONGOING,
        )
        interaction_date = self.current_date - relativedelta(days=days)
        with freeze_time(interaction_date):
            InvestmentProjectInteractionFactory(investment_project=project)

        generate_no_recent_interaction_reminders()
        assert mock_create_no_recent_interaction_reminder.call_count == 0

    def test_stores_notification_id(
        self,
        async_queue,
        caplog,
        mock_reminder_tasks_notify_gateway,
        adviser,
    ):
        """
        Test if a notification id is being stored against the reminder.
        """
        caplog.set_level(logging.INFO, logger='datahub.reminder.tasks')
        notification_id = uuid.uuid4()
        mock_reminder_tasks_notify_gateway.send_email_notification = mock.Mock(
            return_value={'id': notification_id},
        )

        days = 5
        NoRecentInvestmentInteractionSubscriptionFactory(
            adviser=adviser,
            reminder_days=[days],
            email_reminders_enabled=True,
        )
        project = ActiveInvestmentProjectFactory(
            project_manager=adviser,
            status=InvestmentProject.Status.ONGOING,
        )
        interaction_date = self.current_date - relativedelta(days=days)
        with freeze_time(interaction_date):
            InvestmentProjectInteractionFactory(investment_project=project)
        generate_no_recent_interaction_reminders()
        reminder = NoRecentInvestmentInteractionReminder.objects.get(
            project=project,
            adviser=adviser,
        )
        assert any(
            'Task update_no_recent_interaction_reminder_email_status completed'
            f'email_notification_id to {notification_id} and '
            f"reminder_ids set to [UUID('{reminder.id}')]" in message
            for message in caplog.messages
        )
        assert reminder.email_notification_id == notification_id
        assert reminder.email_delivery_status == EmailDeliveryStatus.UNKNOWN

    def test_does_not_send_multiple(
        self,
        async_queue,
        caplog,
        mock_send_no_recent_interaction_reminder,
        mock_reminder_tasks_notify_gateway,
        adviser,
    ):
        """
        Only one reminder should be created.

        Even after calling the generate function multiple times, only one reminder
        should be created and one email sent.
        """
        notification_id = uuid.uuid4()
        mock_reminder_tasks_notify_gateway.send_email_notification = mock.Mock(
            return_value={'id': notification_id},
        )
        days = 5
        NoRecentInvestmentInteractionSubscriptionFactory(
            adviser=adviser,
            reminder_days=[days],
            email_reminders_enabled=True,
        )
        project = ActiveInvestmentProjectFactory(
            project_manager=adviser,
            status=InvestmentProject.Status.ONGOING,
        )
        interaction_date = self.current_date - relativedelta(days=days)
        with freeze_time(interaction_date):
            InvestmentProjectInteractionFactory(investment_project=project)

        generate_no_recent_interaction_reminders()
        generate_no_recent_interaction_reminders()
        reminders = NoRecentInvestmentInteractionReminder.objects.filter(
            project=project,
            adviser=adviser,
        )
        assert reminders.count() == 1
        mock_send_no_recent_interaction_reminder.assert_called_once_with(
            project=project,
            adviser=adviser,
            reminder_days=days,
            current_date=self.current_date,
            reminders=[reminders[0]],
        )


@pytest.mark.django_db
@freeze_time('2022-07-01T10:00:00')
class TestUpdateEmailDeliveryStatusTask:
    current_date = datetime.date(year=2022, month=7, day=17)

    def test_doesnt_update_estimated_land_date_status_without_feature_flag(self, caplog):
        """
        Test that if the feature flag is not enabled, the
        task will not run.
        """
        caplog.set_level(logging.INFO, logger='datahub.reminder.tasks')
        update_notify_email_delivery_status_for_estimated_land_date()
        assert caplog.messages == [
            f'Feature flag {INVESTMENT_ESTIMATED_LAND_DATE_EMAIL_STATUS_FEATURE_FLAG_NAME}'
            ' is not active, exiting.',
        ]

    def test_updates_email_delivery_status_for_estimated_land_date(
        self,
        estimated_land_date_email_status_feature_flag,
        mock_reminder_tasks_notify_gateway,
        adviser,
    ):
        """
        Test if email delivery status is being updated.
        """
        mock_reminder_tasks_notify_gateway.get_notification_by_id = mock.Mock(
            return_value={'status': 'delivered'},
        )

        with freeze_time(self.current_date - relativedelta(days=6)):
            reminder_too_old = UpcomingEstimatedLandDateReminderFactory(
                adviser=adviser,
                email_notification_id=uuid.uuid4(),
            )

        with freeze_time(self.current_date - relativedelta(days=3)):
            reminders_to_update = UpcomingEstimatedLandDateReminderFactory.create_batch(
                2,
                adviser=adviser,
                email_notification_id=uuid.uuid4(),
            )

        status_updated_on = self.current_date - relativedelta(days=1)
        with freeze_time(status_updated_on):
            update_notify_email_delivery_status_for_estimated_land_date()

        with freeze_time(self.current_date):
            update_notify_email_delivery_status_for_estimated_land_date()

        reminder_too_old.refresh_from_db()
        [reminder_to_update.refresh_from_db() for reminder_to_update in reminders_to_update]

        assert reminder_too_old.email_delivery_status == EmailDeliveryStatus.UNKNOWN
        assert all(
            reminder_to_update.email_delivery_status == EmailDeliveryStatus.DELIVERED
            for reminder_to_update in reminders_to_update
        )
        assert all(
            reminder_to_update.modified_on
            == datetime.datetime.combine(
                status_updated_on,
                datetime.datetime.min.time(),
                tzinfo=utc,
            )
            for reminder_to_update in reminders_to_update
        )
        mock_reminder_tasks_notify_gateway.get_notification_by_id.assert_called_once_with(
            reminders_to_update[0].email_notification_id,
            notify_service_name=NotifyServiceName.investment,
        )

    def test_doesnt_update_no_recent_interaction_status_without_feature_flag(self, caplog):
        """
        Test that if the feature flag is not enabled, the
        task will not run.
        """
        caplog.set_level(logging.INFO, logger='datahub.reminder.tasks')
        update_notify_email_delivery_status_for_no_recent_interaction()
        assert caplog.messages == [
            f'Feature flag {INVESTMENT_NO_RECENT_INTERACTION_REMINDERS_EMAIL_STATUS_FLAG_NAME}'
            ' is not active, exiting.',
        ]

    def test_updates_email_delivery_status_for_no_recent_interaction(
        self,
        no_recent_interaction_email_status_feature_flag,
        mock_reminder_tasks_notify_gateway,
        adviser,
    ):
        """
        Test if email delivery status is being updated.
        """
        mock_reminder_tasks_notify_gateway.get_notification_by_id = mock.Mock(
            return_value={'status': 'delivered'},
        )

        with freeze_time(self.current_date - relativedelta(days=6)):
            reminder_too_old = NoRecentInvestmentInteractionReminderFactory(
                adviser=adviser,
                email_notification_id=uuid.uuid4(),
            )

        with freeze_time(self.current_date - relativedelta(days=3)):
            reminder_to_update = NoRecentInvestmentInteractionReminderFactory(
                adviser=adviser,
                email_notification_id=uuid.uuid4(),
            )

        status_updated_on = self.current_date - relativedelta(days=1)
        with freeze_time(status_updated_on):
            update_notify_email_delivery_status_for_no_recent_interaction()

        with freeze_time(self.current_date):
            update_notify_email_delivery_status_for_no_recent_interaction()

        reminder_too_old.refresh_from_db()
        reminder_to_update.refresh_from_db()

        assert reminder_too_old.email_delivery_status == EmailDeliveryStatus.UNKNOWN
        assert reminder_to_update.email_delivery_status == EmailDeliveryStatus.DELIVERED
        assert reminder_to_update.modified_on == datetime.datetime.combine(
            status_updated_on,
            datetime.datetime.min.time(),
            tzinfo=utc,
        )
        mock_reminder_tasks_notify_gateway.get_notification_by_id.assert_called_once_with(
            reminder_to_update.email_notification_id,
            notify_service_name=NotifyServiceName.investment,
        )

    @pytest.mark.parametrize(
        'lock_acquired',
        (False, True),
    )
    def test_lock_for_no_recent_export_interaction_status(
        self,
        no_recent_export_interaction_email_status_feature_flag,
        mock_reminder_tasks_notify_gateway,
        caplog,
        monkeypatch,
        lock_acquired,
        mock_job_scheduler,
        adviser,
    ):
        """
        Test that the task doesn't run if it cannot acquire
        the advisory_lock.
        """
        mock_reminder_tasks_notify_gateway.get_notification_by_id = mock.Mock(
            return_value={'status': 'delivered'},
        )

        caplog.set_level(logging.INFO, logger='datahub.reminder.tasks')
        mock_job_scheduler.return_value = Mock(id=1234)

        with freeze_time(self.current_date - relativedelta(days=3)):
            NoRecentExportInteractionReminderFactory(
                adviser=adviser,
                email_notification_id=uuid.uuid4(),
            )

        mock_advisory_lock = mock.MagicMock()
        mock_advisory_lock.return_value.__enter__.return_value = lock_acquired
        monkeypatch.setattr(
            'datahub.reminder.tasks.advisory_lock',
            mock_advisory_lock,
        )
        with freeze_time(self.current_date):
            update_notify_email_delivery_status_for_no_recent_export_interaction()
        expected_messages = (
            []
            if lock_acquired
            else [
                'Email status checks for no recent export interaction are already being processed'
                ' by another worker.',
            ]
        )
        assert caplog.messages == expected_messages
        if lock_acquired:
            mock_reminder_tasks_notify_gateway.get_notification_by_id.assert_called_once()
        else:
            mock_reminder_tasks_notify_gateway.get_notification_by_id.assert_not_called()

    def test_doesnt_update_no_recent_export_interaction_status_without_feature_flag(self, caplog):
        """
        Test that if the feature flag is not enabled, the task will not run.
        """
        caplog.set_level(logging.INFO, logger='datahub.reminder.tasks')
        update_notify_email_delivery_status_for_no_recent_export_interaction()
        assert caplog.messages == [
            f'Feature flag {EXPORT_NO_RECENT_INTERACTION_REMINDERS_EMAIL_STATUS_FLAG_NAME}'
            ' is not active, exiting.',
        ]

    def test_updates_email_delivery_status_for_no_recent_export_interaction(
        self,
        no_recent_export_interaction_email_status_feature_flag,
        mock_reminder_tasks_notify_gateway,
        adviser,
    ):
        """
        Test if email delivery status is being updated.
        """
        mock_reminder_tasks_notify_gateway.get_notification_by_id = mock.Mock(
            return_value={'status': 'delivered'},
        )

        with freeze_time(self.current_date - relativedelta(days=6)):
            reminder_too_old = NoRecentExportInteractionReminderFactory(
                adviser=adviser,
                email_notification_id=uuid.uuid4(),
            )

        with freeze_time(self.current_date - relativedelta(days=3)):
            reminder_to_update = NoRecentExportInteractionReminderFactory(
                adviser=adviser,
                email_notification_id=uuid.uuid4(),
            )

        status_updated_on = self.current_date - relativedelta(days=1)
        with freeze_time(status_updated_on):
            update_notify_email_delivery_status_for_no_recent_export_interaction()

        with freeze_time(self.current_date):
            update_notify_email_delivery_status_for_no_recent_export_interaction()
        reminder_too_old.refresh_from_db()
        reminder_to_update.refresh_from_db()

        assert reminder_too_old.email_delivery_status == EmailDeliveryStatus.UNKNOWN
        assert reminder_to_update.email_delivery_status == EmailDeliveryStatus.DELIVERED
        assert reminder_to_update.modified_on == datetime.datetime.combine(
            status_updated_on,
            datetime.datetime.min.time(),
            tzinfo=utc,
        )
        mock_reminder_tasks_notify_gateway.get_notification_by_id.assert_called_once_with(
            reminder_to_update.email_notification_id,
            notify_service_name=NotifyServiceName.investment,
        )

    def test_doesnt_update_new_export_interaction_status_without_feature_flag(self, caplog):
        """
        Test that if the feature flag is not enabled, the task will not run.
        """
        caplog.set_level(logging.INFO, logger='datahub.reminder.tasks')
        update_notify_email_delivery_status_for_new_export_interaction()
        assert caplog.messages == [
            f'Feature flag {EXPORT_NEW_INTERACTION_REMINDERS_EMAIL_STATUS_FLAG_NAME}'
            ' is not active, exiting.',
        ]

    @pytest.mark.parametrize(
        'lock_acquired',
        (False, True),
    )
    def test_lock_for_new_export_interaction_status(
        self,
        new_export_interaction_email_status_feature_flag,
        mock_reminder_tasks_notify_gateway,
        caplog,
        monkeypatch,
        lock_acquired,
        mock_job_scheduler,
        adviser,
    ):
        """
        Test that the task doesn't run if it cannot acquire
        the advisory_lock.
        """
        mock_reminder_tasks_notify_gateway.get_notification_by_id = mock.Mock(
            return_value={'status': 'delivered'},
        )

        caplog.set_level(logging.INFO, logger='datahub.reminder.tasks')
        mock_job_scheduler.return_value = Mock(id=1234)

        with freeze_time(self.current_date - relativedelta(days=3)):
            NewExportInteractionReminderFactory(
                adviser=adviser,
                email_notification_id=uuid.uuid4(),
            )

        mock_advisory_lock = mock.MagicMock()
        mock_advisory_lock.return_value.__enter__.return_value = lock_acquired
        monkeypatch.setattr(
            'datahub.reminder.tasks.advisory_lock',
            mock_advisory_lock,
        )
        with freeze_time(self.current_date):
            update_notify_email_delivery_status_for_new_export_interaction()
        expected_messages = (
            []
            if lock_acquired
            else [
                'Email status checks for new export interaction are already being processed'
                ' by another worker.',
            ]
        )
        assert caplog.messages == expected_messages

        if lock_acquired:
            mock_reminder_tasks_notify_gateway.get_notification_by_id.assert_called_once()
        else:
            mock_reminder_tasks_notify_gateway.get_notification_by_id.assert_not_called()

    def test_updates_email_delivery_status_for_new_export_interaction(
        self,
        new_export_interaction_email_status_feature_flag,
        mock_reminder_tasks_notify_gateway,
        adviser,
    ):
        """
        Test if email delivery status is being updated.
        """
        mock_reminder_tasks_notify_gateway.get_notification_by_id = mock.Mock(
            return_value={'status': 'delivered'},
        )

        with freeze_time(self.current_date - relativedelta(days=6)):
            reminder_too_old = NewExportInteractionReminderFactory(
                adviser=adviser,
                email_notification_id=uuid.uuid4(),
            )

        with freeze_time(self.current_date - relativedelta(days=3)):
            reminder_to_update = NewExportInteractionReminderFactory(
                adviser=adviser,
                email_notification_id=uuid.uuid4(),
            )

        status_updated_on = self.current_date - relativedelta(days=1)
        with freeze_time(status_updated_on):
            update_notify_email_delivery_status_for_new_export_interaction()

        with freeze_time(self.current_date):
            update_notify_email_delivery_status_for_new_export_interaction()
        reminder_too_old.refresh_from_db()
        reminder_to_update.refresh_from_db()

        assert reminder_too_old.email_delivery_status == EmailDeliveryStatus.UNKNOWN
        assert reminder_to_update.email_delivery_status == EmailDeliveryStatus.DELIVERED
        assert reminder_to_update.modified_on == datetime.datetime.combine(
            status_updated_on,
            datetime.datetime.min.time(),
            tzinfo=utc,
        )
        mock_reminder_tasks_notify_gateway.get_notification_by_id.assert_called_once_with(
            reminder_to_update.email_notification_id,
            notify_service_name=NotifyServiceName.investment,
        )
