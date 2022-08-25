from unittest import mock
from uuid import uuid4

import pytest
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.test.utils import override_settings
from django.utils.timesince import timesince
from django.utils.timezone import now

from datahub.company.test.factories import AdviserFactory
from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.reminder.emails import get_projects_summary_list
from datahub.reminder.tasks import (
    send_estimated_land_date_reminder,
    send_estimated_land_date_summary,
    send_no_recent_interaction_reminder,
)

pytestmark = pytest.mark.django_db


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
        mock_notify_adviser_by_email,
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
                    'estimated_land_date': project.estimated_land_date.strftime('%-d %B %Y'),
                },
                None,
            )
            mock_statsd.incr.assert_called_once_with('send_investment_notification.30')

    def test_sends_estimated_land_date_summary_notification(
        self,
        mock_notify_adviser_by_email,
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

            mock_notify_adviser_by_email.assert_called_once_with(
                adviser,
                template_id,
                {
                    'month': current_date.strftime('%B'),
                    'reminders_number': len(notifications),
                    'summary': ''.join(notifications),
                    'settings_url': settings.DATAHUB_FRONTEND_REMINDER_SETTINGS_URL,
                },
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
                    'estimated_land_date': project.estimated_land_date.strftime('%-d %B %Y'),
                    'time_period': timesince(
                        last_interaction_date,
                        now=current_date,
                    ).split(',')[0],
                    'last_interaction_date': last_interaction_date.strftime('%-d %B %Y'),
                },
                None,
            )
            mock_statsd.incr.assert_called_once_with('send_no_recent_interaction_notification.5')
