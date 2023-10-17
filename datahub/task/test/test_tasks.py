import datetime
from unittest import mock
from unittest.mock import ANY
from uuid import uuid4


import pytest

from django.test.utils import override_settings

from datahub.feature_flag.test.factories import UserFeatureFlagFactory
from datahub.reminder import ADVISER_TASKS_USER_FEATURE_FLAG_NAME
from datahub.reminder.models import UpcomingTaskReminderSubscription
from datahub.reminder.test.factories import UpcomingTaskReminderFactory
from datahub.task.tasks import generate_reminders_upcoming_tasks, update_task_reminder_email_status
from datahub.task.test.factories import AdviserFactory, InvestmentProjectTaskFactory, TaskFactory


@pytest.fixture()
def adviser_tasks_user_feature_flag():
    """
    Creates the adviser task feature flag.
    """
    yield UserFeatureFlagFactory(
        code=ADVISER_TASKS_USER_FEATURE_FLAG_NAME,
        is_active=True,
    )


# When feature flag is removed replace calls with AdviserFactory
def add_user_feature_flag(adviser_tasks_user_feature_flag, adviser):
    adviser.features.set([adviser_tasks_user_feature_flag])
    return adviser


@pytest.fixture
def mock_notify_adviser_by_rq_email(monkeypatch):
    """
    Mocks the notify_adviser_by_rq_email function.
    """
    mock_notify_adviser_by_rq_email = mock.Mock()
    monkeypatch.setattr(
        'datahub.task.tasks.notify_adviser_by_rq_email',
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


def investment_project_factory_due_today(days=1, advisers=None):
    if not advisers:
        advisers = [AdviserFactory()]
    return InvestmentProjectTaskFactory(
        task=TaskFactory(
            due_date=datetime.date.today() + datetime.timedelta(days=days),
            reminder_days=days,
            advisers=advisers,
        ),
    )


def mock_notify_adviser_email_call(investment_project_task_due, matching_adviser, template_id):
    reminder = UpcomingTaskReminderFactory(
        adviser=matching_adviser,
        task=investment_project_task_due.task,
        event=f'{investment_project_task_due.task.reminder_days} days left to task due',
    )
    reminder.id = ANY
    reminder.pk = ANY

    return mock.call(
        adviser=matching_adviser,
        template_identifier=template_id,
        context={
            'task_title': investment_project_task_due.task.title,
            'company_name': investment_project_task_due.investment_project.investor_company.name,
            'task_due_date': investment_project_task_due.task.due_date,
            'company_contact_email_address': '',
            'task_url': investment_project_task_due.task.get_absolute_url(),
            'complete_task_url': investment_project_task_due.task.get_absolute_url(),
        },
        update_task=update_task_reminder_email_status,
        reminders=[reminder],
    )


@pytest.mark.django_db
class TestTaskReminders:
    def test_generate_reminders_for_upcoming_tasks(
        self,
        adviser_tasks_user_feature_flag,
        mock_notify_adviser_by_rq_email,
        mock_statsd,
    ):
        # create a few tasks without due reminders
        # create a few tasks with due reminders
        tasks = InvestmentProjectTaskFactory.create_batch(4)
        tasks_due = []
        matching_advisers = AdviserFactory.create_batch(3)
        matching_advisers = [add_user_feature_flag(adviser_tasks_user_feature_flag, adviser)
                             for adviser in matching_advisers]
        tasks_due.append(investment_project_factory_due_today(1, advisers=[matching_advisers[0]]))
        tasks_due.append(investment_project_factory_due_today(7, advisers=[matching_advisers[1]]))
        tasks_due.append(investment_project_factory_due_today(30, advisers=matching_advisers))

        template_id = str(uuid4())
        with override_settings(
            TASK_REMINDER_STATUS_TEMPLATE_ID=template_id,
        ):
            tasks = generate_reminders_upcoming_tasks()

            assert tasks.count() == 3

        mock_notify_adviser_by_rq_email.assert_has_calls(
            [
                mock_notify_adviser_email_call(tasks_due[0], matching_advisers[0], template_id),
                mock_notify_adviser_email_call(tasks_due[1], matching_advisers[1], template_id),
                mock_notify_adviser_email_call(tasks_due[2], matching_advisers[0], template_id),
                mock_notify_adviser_email_call(tasks_due[2], matching_advisers[1], template_id),
                mock_notify_adviser_email_call(tasks_due[2], matching_advisers[2], template_id),
            ],
            any_order=True,
        )

    def test_emails_not_send_when_email_subscription_not_enabled_by_adviser(
        self,
        adviser_tasks_user_feature_flag,
        mock_notify_adviser_by_rq_email,
        mock_statsd,
    ):
        matching_advisers = AdviserFactory.create_batch(2)
        matching_advisers = [add_user_feature_flag(adviser_tasks_user_feature_flag, adviser)
                             for adviser in matching_advisers]
        task_due = investment_project_factory_due_today(1, advisers=matching_advisers)
        subscription = UpcomingTaskReminderSubscription.objects.filter(
            adviser=matching_advisers[1],
        ).first()
        subscription.email_reminders_enabled = False
        subscription.save()

        template_id = str(uuid4())
        with override_settings(
            TASK_REMINDER_STATUS_TEMPLATE_ID=template_id,
        ):
            generate_reminders_upcoming_tasks()

        mock_notify_adviser_by_rq_email.assert_has_calls([
            mock_notify_adviser_email_call(task_due, matching_advisers[0], template_id),
        ])
        mock_notify_adviser_by_rq_email.assert_called_once()

    def test_task_reminder_emails_only_sent_if_feature_flag_set(
        self,
        adviser_tasks_user_feature_flag,
        mock_notify_adviser_by_rq_email,
        mock_statsd,
    ):
        matching_advisers = AdviserFactory.create_batch(2)
        matching_advisers[0] = add_user_feature_flag(
            adviser_tasks_user_feature_flag, matching_advisers[0],
        )

        task_due = investment_project_factory_due_today(1, advisers=matching_advisers)
        subscription = UpcomingTaskReminderSubscription.objects.filter(
            adviser=matching_advisers[1],
        ).first()
        subscription.email_reminders_enabled = False
        subscription.save()

        template_id = str(uuid4())
        with override_settings(
            TASK_REMINDER_STATUS_TEMPLATE_ID=template_id,
        ):
            generate_reminders_upcoming_tasks()

        mock_notify_adviser_by_rq_email.assert_has_calls([
            mock_notify_adviser_email_call(task_due, matching_advisers[0], template_id),
        ])
        mock_notify_adviser_by_rq_email.assert_called_once()

    def test_update_task_reminder_email_status_set(self, adviser_tasks_user_feature_flag):
        # Test that the update_task_reminder_email_status method is called from
        # send_task_reminder_email
        pass

    # tasks [due_date - reminder_days = today]
    #   advisers [is_active && ]
    #       upcoming_task_reminder_subscription [select email_reminder_enabled]

    #   userfeatureflag or userfeatureflag group set

    # Add reminder to DataHub reminders
    # Send email if upcoming_task_reminder_subscription.email_reminder_enabled
