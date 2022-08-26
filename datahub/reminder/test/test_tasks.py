import datetime
import uuid
from operator import attrgetter
from unittest import mock
from unittest.mock import ANY, call

import factory
import pytest
from dateutil.relativedelta import relativedelta
from freezegun import freeze_time

from datahub.company.test.factories import AdviserFactory
from datahub.core.constants import InvestmentProjectStage
from datahub.feature_flag.test.factories import UserFeatureFlagFactory
from datahub.interaction.test.factories import InvestmentProjectInteractionFactory
from datahub.investment.project.models import InvestmentProject
from datahub.investment.project.test.factories import (
    ActiveInvestmentProjectFactory,
    InvestmentProjectFactory,
)
from datahub.reminder import (
    ESTIMATED_LAND_DATE_REMINDERS_FEATURE_FLAG_NAME,
    NO_RECENT_INTERACTION_REMINDERS_FEATURE_FLAG_NAME,
)
from datahub.reminder.models import (
    EmailDeliveryStatus,
    NoRecentInvestmentInteractionReminder,
    UpcomingEstimatedLandDateReminder,
)
from datahub.reminder.tasks import (
    create_estimated_land_date_reminder,
    create_no_recent_interaction_reminder,
    generate_estimated_land_date_reminders,
    generate_estimated_land_date_reminders_for_subscription,
    generate_no_recent_interaction_reminders,
    generate_no_recent_interaction_reminders_for_subscription,
)
from datahub.reminder.test.factories import (
    NoRecentInvestmentInteractionSubscriptionFactory,
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
def no_recent_interaction_reminders_user_feature_flag():
    """
    Creates the no recent interaction reminders user feature flag.
    """
    yield UserFeatureFlagFactory(
        code=NO_RECENT_INTERACTION_REMINDERS_FEATURE_FLAG_NAME,
        is_active=True,
    )


@pytest.fixture()
def adviser(
    no_recent_interaction_reminders_user_feature_flag,
    estimated_land_date_reminders_user_feature_flag,
):
    """
    An adviser with the relevant feature flags enabled
    """
    adviser = AdviserFactory()
    adviser.features.set(
        [
            estimated_land_date_reminders_user_feature_flag,
            no_recent_interaction_reminders_user_feature_flag,
        ],
    )
    return adviser


@pytest.fixture()
def inactive_adviser(
    no_recent_interaction_reminders_user_feature_flag,
    estimated_land_date_reminders_user_feature_flag,
):
    """
    An inactive adviser with the relevant feature flags enabled
    """
    inactive_adviser = AdviserFactory(is_active=False)
    inactive_adviser.features.set(
        [
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
def mock_generate_estimated_land_date_reminders_for_subscription(monkeypatch):
    mock_generate_estimated_land_date_reminders_for_subscription = mock.Mock()
    monkeypatch.setattr(
        'datahub.reminder.tasks.generate_estimated_land_date_reminders_for_subscription',
        mock_generate_estimated_land_date_reminders_for_subscription,
    )
    return mock_generate_estimated_land_date_reminders_for_subscription


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
def mock_notify_gateway(monkeypatch):
    mock_notify_gateway = mock.Mock()
    monkeypatch.setattr(
        'datahub.notification.tasks.notify_gateway',
        mock_notify_gateway,
    )
    return mock_notify_gateway


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

        mock_create_estimated_land_date_reminder.assert_has_calls([
            call(
                project=project,
                adviser=adviser,
                send_email=False,
                current_date=self.current_date,
            )
            for project in projects
        ], any_order=True)

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
        mock_create_estimated_land_date_reminder.assert_has_calls([
            call(
                project=project,
                adviser=adviser,
                send_email=True,
                current_date=self.current_date,
            )
            for project in [active_ongoing_project, active_delayed_project]
        ], any_order=True)

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
        assert UpcomingEstimatedLandDateReminder.objects.filter(
            project=project,
            adviser=adviser,
        ).count() == 1
        reminder = UpcomingEstimatedLandDateReminder.objects.get(project=project, adviser=adviser)
        mock_send_estimated_land_date_reminder.assert_called_once_with(
            project=project,
            adviser=adviser,
            days_left=days,
            reminders=[reminder],
        )

    def test_stores_notification_id(
        self,
        mock_notify_gateway,
        adviser,
    ):
        """
        Test if a notification id is being stored against the reminder.
        """
        notification_id = uuid.uuid4()
        mock_notify_gateway.send_email_notification = mock.Mock(
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
        mock_notify_gateway,
        adviser,
    ):
        """
        Test if a notification id is being stored against the reminders from summary email.
        """
        notification_id = uuid.uuid4()
        mock_notify_gateway.send_email_notification = mock.Mock(
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
        mock_generate_no_recent_interaction_reminders_for_subscription,
    ):
        """
        Reminders should be generated for all subscriptions.
        """
        subscription_count = 2
        subscriptions = NoRecentInvestmentInteractionSubscriptionFactory.create_batch(
            subscription_count,
        )
        generate_no_recent_interaction_reminders()
        mock_generate_no_recent_interaction_reminders_for_subscription.assert_has_calls(
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
        mock_create_no_recent_interaction_reminder.assert_has_calls([
            call(
                project=project,
                adviser=adviser,
                reminder_days=day,
                send_email=True,
                current_date=self.current_date,
            )
            for project in [active_ongoing_project, active_delayed_project]
        ], any_order=True)

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
            code=NO_RECENT_INTERACTION_REMINDERS_FEATURE_FLAG_NAME,
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
        mock_notify_gateway,
        adviser,
    ):
        """
        Test if a notification id is being stored against the reminder.
        """
        notification_id = uuid.uuid4()
        mock_notify_gateway.send_email_notification = mock.Mock(
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
        assert reminder.email_notification_id == notification_id
        assert reminder.email_delivery_status == EmailDeliveryStatus.UNKNOWN

    def test_does_not_send_multiple(
        self,
        mock_send_no_recent_interaction_reminder,
        adviser,
    ):
        """
        Only one reminder should be created.

        Even after calling the generate function multiple times, only one reminder
        should be created and one email sent.
        """
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
