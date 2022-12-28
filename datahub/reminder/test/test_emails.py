from unittest import mock
from uuid import uuid4

import pytest
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.test.utils import override_settings
from django.utils.timesince import timesince
from django.utils.timezone import now

from datahub.company.test.factories import (
    AdviserFactory,
    OneListCoreTeamMemberFactory,
)
from datahub.core.queues.scheduler import LONG_RUNNING_QUEUE
from datahub.interaction.test.factories import CompanyInteractionFactory
from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.notification.constants import NotifyServiceName
from datahub.reminder.emails import get_projects_summary_list
from datahub.reminder.models import NoRecentExportInteractionReminder
from datahub.reminder.tasks import (
    notify_adviser_by_rq_email,
    send_email_notification_via_rq,
    send_estimated_land_date_reminder,
    send_estimated_land_date_summary,
    send_no_recent_export_interaction_reminder,
    send_no_recent_interaction_reminder,
    update_estimated_land_date_reminder_email_status,
    update_no_recent_export_interaction_reminder_email_status,
)
from datahub.reminder.test.factories import NoRecentExportInteractionReminderFactory

pytestmark = pytest.mark.django_db

DATE_FORMAT = '%-d %B %Y'


@pytest.fixture()
def mock_notify_gateway(monkeypatch):
    mock_notify_gateway = mock.Mock()
    monkeypatch.setattr(
        'datahub.reminder.tasks.notify_gateway',
        mock_notify_gateway,
    )
    return mock_notify_gateway


@pytest.fixture
def mock_job_scheduler(monkeypatch):
    """
    Mocks the job_scheduler function.
    """
    mock_job_scheduler = mock.Mock()
    monkeypatch.setattr(
        'datahub.reminder.tasks.job_scheduler',
        mock_job_scheduler,
    )
    return mock_job_scheduler


@pytest.fixture
def mock_notify_adviser_by_email(monkeypatch):
    """
    Mocks the notify_adviser_by_email function.
    """
    mock_notify_adviser_by_email = mock.Mock()
    monkeypatch.setattr(
        'datahub.reminder.tasks.notify_adviser_by_email',
        mock_notify_adviser_by_email,
    )
    return mock_notify_adviser_by_email


@pytest.fixture
def mock_notify_adviser_by_rq_email(monkeypatch):
    """
    Mocks the notify_adviser_by_rq_email function.
    """
    mock_notify_adviser_by_rq_email = mock.Mock()
    monkeypatch.setattr(
        'datahub.reminder.tasks.notify_adviser_by_rq_email',
        mock_notify_adviser_by_rq_email,
    )
    return mock_notify_adviser_by_rq_email


@pytest.fixture
def mock_statsd(monkeypatch):
    """
    Returns a mock statsd client instance.
    """
    mock_statsd = mock.Mock()
    monkeypatch.setattr(
        'datahub.reminder.tasks.statsd',
        mock_statsd,
    )
    return mock_statsd


class TestEmailFunctions:
    """Test email notification sending functions."""

    def test_sends_estimated_land_date_notification(
        self,
        mock_notify_adviser_by_rq_email,
        # mock_notify_adviser_by_email,
        mock_statsd,
    ):
        """Test it sends an estimated land date notification."""
        adviser = AdviserFactory()
        project = InvestmentProjectFactory()

        template_id = str(uuid4())
        with override_settings(
            INVESTMENT_NOTIFICATION_ESTIMATED_LAND_DATE_TEMPLATE_ID=template_id,
        ):
            send_estimated_land_date_reminder(
                project=project,
                adviser=adviser,
                days_left=30,
                reminders=None,
            )

            mock_notify_adviser_by_rq_email.assert_called_once_with(
                adviser,
                template_id,
                {
                    'project_details_url': f'{project.get_absolute_url()}/details',
                    'settings_url': settings.DATAHUB_FRONTEND_REMINDER_SETTINGS_URL,
                    'investor_company_name': project.investor_company.name,
                    'project_name': project.name,
                    'project_code': project.project_code,
                    'project_status': project.status.capitalize(),
                    'project_stage': project.stage.name,
                    'estimated_land_date': project.estimated_land_date.strftime(DATE_FORMAT),
                },
                update_estimated_land_date_reminder_email_status,
                None,
            )
            mock_statsd.incr.assert_called_once_with('send_investment_notification.30')

    def test_sends_estimated_land_date_summary_notification(
        self,
        mock_notify_adviser_by_rq_email,
        mock_statsd,
    ):
        """Test it sends an estimated land date summary notification."""
        adviser = AdviserFactory()
        projects = InvestmentProjectFactory.create_batch(2)

        notifications = get_projects_summary_list(projects)

        current_date = now().date()

        template_id = str(uuid4())
        with override_settings(
            INVESTMENT_NOTIFICATION_ESTIMATED_LAND_DATE_SUMMARY_TEMPLATE_ID=template_id,
        ):
            send_estimated_land_date_summary(
                projects=projects,
                adviser=adviser,
                current_date=current_date,
                reminders=None,
            )

            mock_notify_adviser_by_rq_email.assert_called_once_with(
                adviser,
                template_id,
                {
                    'month': current_date.strftime('%B'),
                    'reminders_number': len(notifications),
                    'summary': ''.join(notifications),
                    'settings_url': settings.DATAHUB_FRONTEND_REMINDER_SETTINGS_URL,
                },
                update_estimated_land_date_reminder_email_status,
                None,
            )
            mock_statsd.incr.assert_called_once_with('send_estimated_land_date_summary')

    def test_sends_no_recent_interaction_notification(
        self,
        mock_notify_adviser_by_email,
        mock_statsd,
    ):
        """Test it sends a no recent interaction notification."""
        adviser = AdviserFactory()
        project = InvestmentProjectFactory()

        current_date = now().date()
        last_interaction_date = current_date - relativedelta(days=5)

        template_id = str(uuid4())
        with override_settings(
            INVESTMENT_NOTIFICATION_NO_RECENT_INTERACTION_TEMPLATE_ID=template_id,
        ):
            send_no_recent_interaction_reminder(
                project=project,
                adviser=adviser,
                reminder_days=5,
                current_date=current_date,
                reminders=None,
            )

            mock_notify_adviser_by_email.assert_called_once_with(
                adviser,
                template_id,
                {
                    'project_details_url': f'{project.get_absolute_url()}/details',
                    'settings_url': settings.DATAHUB_FRONTEND_REMINDER_SETTINGS_URL,
                    'investor_company_name': project.investor_company.name,
                    'project_name': project.name,
                    'project_code': project.project_code,
                    'project_status': project.status.capitalize(),
                    'project_stage': project.stage.name,
                    'estimated_land_date': project.estimated_land_date.strftime(DATE_FORMAT),
                    'time_period': timesince(
                        last_interaction_date,
                        now=current_date,
                    ).split(',')[0],
                    'last_interaction_date': last_interaction_date.strftime(DATE_FORMAT),
                },
                None,
            )
            mock_statsd.incr.assert_called_once_with('send_no_recent_interaction_notification.5')

    def test_sends_no_recent_export_interaction_notification(
        self,
        mock_notify_adviser_by_rq_email,
        mock_statsd,
    ):
        """Test it sends a no recent export interaction notification."""
        days = 5
        adviser = AdviserFactory()
        company = OneListCoreTeamMemberFactory(adviser=adviser).company
        interaction = CompanyInteractionFactory(company=company)

        current_date = now().date()
        last_interaction_date = current_date - relativedelta(days=days)

        template_id = str(uuid4())
        with override_settings(EXPORT_NOTIFICATION_NO_RECENT_INTERACTION_TEMPLATE_ID=template_id):
            send_no_recent_export_interaction_reminder(
                company=company,
                interaction=interaction,
                adviser=adviser,
                reminder_days=days,
                current_date=current_date,
                reminders=None,
            )
            mock_notify_adviser_by_rq_email.assert_called_once_with(
                adviser,
                template_id,
                {
                    'company_name': company.name,
                    'company_url': f'{company.get_absolute_url()}/details',
                    'last_interaction_date': last_interaction_date.strftime(DATE_FORMAT),
                    'last_interaction_created_by': interaction.created_by.name,
                    'last_interaction_type': interaction.get_kind_display(),
                    'last_interaction_subject': interaction.subject,
                    'settings_url': settings.DATAHUB_FRONTEND_REMINDER_SETTINGS_URL,
                    'time_period': timesince(
                        last_interaction_date,
                        now=current_date,
                    ).split(',')[0],
                },
                update_no_recent_export_interaction_reminder_email_status,
                None,
            )
            mock_statsd.incr.assert_called_once_with(
                'send_no_recent_export_interaction_notification.5',
            )

    def test_sends_no_export_interaction_notification(
        self,
        mock_notify_adviser_by_rq_email,
        mock_statsd,
    ):
        """
        Test it sends a no recent export interaction notification
        where there are no interactions at all.
        """
        days = 5
        adviser = AdviserFactory()
        company = OneListCoreTeamMemberFactory(adviser=adviser).company

        current_date = now().date()
        last_interaction_date = current_date - relativedelta(days=days)

        template_id = str(uuid4())
        with override_settings(EXPORT_NOTIFICATION_NO_INTERACTION_TEMPLATE_ID=template_id):
            send_no_recent_export_interaction_reminder(
                company=company,
                interaction=None,
                adviser=adviser,
                reminder_days=days,
                current_date=current_date,
                reminders=None,
            )
            mock_notify_adviser_by_rq_email.assert_called_once_with(
                adviser,
                template_id,
                {
                    'company_name': company.name,
                    'company_url': f'{company.get_absolute_url()}/details',
                    'last_interaction_date': last_interaction_date.strftime(DATE_FORMAT),
                    'settings_url': settings.DATAHUB_FRONTEND_REMINDER_SETTINGS_URL,
                    'time_period': timesince(
                        last_interaction_date,
                        now=current_date,
                    ).split(',')[0],
                },
                update_no_recent_export_interaction_reminder_email_status,
                None,
            )
            mock_statsd.incr.assert_called_once_with(
                'send_no_recent_export_interaction_notification.5',
            )

    def test_notify_adviser_of_no_recent_export_interactions(
        self,
        mock_job_scheduler,
    ):
        """
        Tests the notify_adviser_by_rq_email function.

        It should schedule a task to:
            * notify an adviser
            * trigger a second task to store the notification_id
        """
        adviser = AdviserFactory()
        template_id = str(uuid4())
        context = {}
        reminders = NoRecentExportInteractionReminderFactory.create_batch(2)

        notify_adviser_by_rq_email(
            adviser,
            template_id,
            context,
            update_no_recent_export_interaction_reminder_email_status,
            reminders,
        )
        mock_job_scheduler.assert_called_once_with(
            function=send_email_notification_via_rq,
            function_args=(
                adviser.get_current_email(),
                template_id,
                update_no_recent_export_interaction_reminder_email_status,
                [reminder.id for reminder in reminders],
                context,
                NotifyServiceName.investment,
            ),
            retry_backoff=True,
            max_retries=5,
        )

        mock_job_scheduler.reset_mock()
        reminders = []
        notify_adviser_by_rq_email(
            adviser,
            template_id,
            context,
            update_no_recent_export_interaction_reminder_email_status,
            reminders,
        )
        mock_job_scheduler.assert_called_once_with(
            function=send_email_notification_via_rq,
            function_args=(
                adviser.get_current_email(),
                template_id,
                update_no_recent_export_interaction_reminder_email_status,
                None,
                context,
                NotifyServiceName.investment,
            ),
            retry_backoff=True,
            max_retries=5,
        )

    def test_send_email_notification_via_rq(
        self,
        mock_notify_gateway,
        mock_job_scheduler,
    ):
        """
        Tests email notification task queued with RQ.

        The id it receives in response should be used to queue a second task
        to update the email delivery status.
        """
        notification_id = str(uuid4())
        mock_notify_gateway.send_email_notification = mock.Mock(
            return_value={'id': notification_id},
        )

        adviser = AdviserFactory()
        template_id = str(uuid4())
        context = {}
        reminders = NoRecentExportInteractionReminderFactory.create_batch(2)

        send_email_notification_via_rq(
            adviser.get_current_email(),
            template_id,
            update_no_recent_export_interaction_reminder_email_status,
            [reminder.id for reminder in reminders],
            context,
            NotifyServiceName.investment,
        )

        mock_notify_gateway.send_email_notification.assert_called_once_with(
            adviser.get_current_email(),
            template_id,
            context,
            NotifyServiceName.investment,
        )

        mock_job_scheduler.assert_called_once_with(
            function=update_no_recent_export_interaction_reminder_email_status,
            function_args=(
                notification_id,
                [reminder.id for reminder in reminders],
            ),
            queue_name=LONG_RUNNING_QUEUE,
            max_retries=5,
            retry_backoff=True,
            retry_intervals=30,
        )

    def test_update_no_recent_export_interaction_reminder_email_status(
        self,
    ):
        """
        Test it updates reminder data with the connected email notification information.
        """
        reminder_number = 3
        notification_id = str(uuid4())
        reminders = NoRecentExportInteractionReminderFactory.create_batch(reminder_number)

        update_no_recent_export_interaction_reminder_email_status(
            notification_id,
            [reminder.id for reminder in reminders],
        )

        NoRecentExportInteractionReminderFactory.create_batch(2)

        linked_reminders = NoRecentExportInteractionReminder.objects.filter(
            email_notification_id=notification_id,
        )
        assert linked_reminders.count() == (reminder_number)
