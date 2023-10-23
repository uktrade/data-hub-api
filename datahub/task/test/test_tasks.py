import datetime
import logging
from importlib import import_module
from unittest import mock
from unittest.mock import ANY, Mock
from uuid import uuid4


import pytest


from django.apps import apps
from django.test.utils import override_settings

from datahub.feature_flag.test.factories import UserFeatureFlagFactory
from datahub.reminder import ADVISER_TASKS_USER_FEATURE_FLAG_NAME
from datahub.reminder.models import UpcomingTaskReminder, UpcomingTaskReminderSubscription
from datahub.reminder.test.factories import UpcomingTaskReminderFactory

from datahub.task.tasks import (
    generate_reminders_upcoming_tasks,
    schedule_reminders_upcoming_tasks,
    update_task_reminder_email_status,
)
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


@pytest.fixture()
def mock_job_scheduler(monkeypatch):
    mock_job_scheduler = mock.Mock()
    monkeypatch.setattr(
        'datahub.task.tasks.job_scheduler',
        mock_job_scheduler,
    )
    return mock_job_scheduler


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
            'task_due_date': investment_project_task_due.task.due_date.strftime('%-d %B %Y'),
            'task_url': investment_project_task_due.task.get_absolute_url(),
        },
        update_task=update_task_reminder_email_status,
        reminders=[reminder],
    )


@pytest.mark.django_db
class TestTaskReminders:
    @pytest.mark.parametrize(
        'lock_acquired',
        (
            False,
            True,
        ),
    )
    def test_lock(
        self,
        caplog,
        monkeypatch,
        lock_acquired,
        adviser_tasks_user_feature_flag,
        mock_notify_adviser_by_rq_email,
    ):
        """
        Test that the task doesn't run if it cannot acquire
        the advisory_lock.
        """
        adviser = AdviserFactory()
        add_user_feature_flag(adviser_tasks_user_feature_flag, adviser)
        investment_project_factory_due_today(1, advisers=[adviser])

        caplog.set_level(logging.INFO, logger='datahub.task.tasks')

        mock_advisory_lock = mock.MagicMock()
        mock_advisory_lock.return_value.__enter__.return_value = lock_acquired
        monkeypatch.setattr(
            'datahub.task.tasks.advisory_lock',
            mock_advisory_lock,
        )

        generate_reminders_upcoming_tasks()
        expected_messages = (
            [
                'Task generate_reminders_upcoming_tasks completed',
            ]
            if lock_acquired
            else [
                'Reminders for upcoming tasks are already being processed by another worker.',
            ]
        )
        assert caplog.messages == expected_messages

        if lock_acquired:
            mock_notify_adviser_by_rq_email.assert_called_once()
        else:
            mock_notify_adviser_by_rq_email.assert_not_called()

    def test_generate_reminders_for_upcoming_tasks(
        self,
        adviser_tasks_user_feature_flag,
        mock_notify_adviser_by_rq_email,
        mock_statsd,
    ):
        # create a few tasks with and without due reminders
        tasks = InvestmentProjectTaskFactory.create_batch(4)
        tasks_due = []
        matching_advisers = AdviserFactory.create_batch(3)
        matching_advisers = [
            add_user_feature_flag(adviser_tasks_user_feature_flag, adviser)
            for adviser in matching_advisers
        ]
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

    def test_emails_only_send_when_email_subscription_enabled_by_adviser(
        self,
        adviser_tasks_user_feature_flag,
        mock_notify_adviser_by_rq_email,
        mock_statsd,
    ):
        # Create two advisers one with and one without an task reminder email subscription
        matching_advisers = AdviserFactory.create_batch(2)
        matching_advisers = [
            add_user_feature_flag(adviser_tasks_user_feature_flag, adviser)
            for adviser in matching_advisers
        ]
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

        mock_notify_adviser_by_rq_email.assert_has_calls(
            [
                mock_notify_adviser_email_call(task_due, matching_advisers[0], template_id),
            ],
        )
        mock_notify_adviser_by_rq_email.assert_called_once()

    def test_task_reminder_emails_only_sent_if_feature_flag_set(
        self,
        adviser_tasks_user_feature_flag,
        mock_notify_adviser_by_rq_email,
        mock_statsd,
    ):
        # Create a adviser with and another without the feature flag set.
        matching_advisers = AdviserFactory.create_batch(2)
        matching_advisers[0] = add_user_feature_flag(
            adviser_tasks_user_feature_flag,
            matching_advisers[0],
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

        mock_notify_adviser_by_rq_email.assert_has_calls(
            [
                mock_notify_adviser_email_call(task_due, matching_advisers[0], template_id),
            ],
        )
        mock_notify_adviser_by_rq_email.assert_called_once()

    def test_if_reminder_already_sent_the_same_day_do_nothing(
        self,
        adviser_tasks_user_feature_flag,
        mock_notify_adviser_by_rq_email,
        mock_statsd,
    ):
        adviser = AdviserFactory()
        adviser = add_user_feature_flag(
            adviser_tasks_user_feature_flag,
            adviser,
        )
        task_due = investment_project_factory_due_today(1, advisers=[adviser])

        template_id = str(uuid4())
        with override_settings(
            TASK_REMINDER_STATUS_TEMPLATE_ID=template_id,
        ):
            generate_reminders_upcoming_tasks()
            generate_reminders_upcoming_tasks()

        mock_notify_adviser_by_rq_email.assert_has_calls(
            [
                mock_notify_adviser_email_call(task_due, adviser, template_id),
            ],
        )
        mock_notify_adviser_by_rq_email.assert_called_once()

    def test_update_task_reminder_email_status(
        self,
    ):
        """
        Test it updates reminder data with the connected email notification information.
        """
        task = TaskFactory()
        reminder_number = 3
        notification_id = str(uuid4())
        reminders = UpcomingTaskReminderFactory.create_batch(reminder_number, task_id=task.id)

        update_task_reminder_email_status(
            notification_id,
            [reminder.id for reminder in reminders],
        )

        task2 = TaskFactory()
        UpcomingTaskReminderFactory.create_batch(2, task_id=task2.id)

        linked_reminders = UpcomingTaskReminder.objects.filter(
            email_notification_id=notification_id,
        )
        assert linked_reminders.count() == (reminder_number)

    def test_schedule_reminders_upcoming_tasks(
        self,
        caplog,
        mock_job_scheduler,
    ):
        """
        Generate reminders upcoming tasks should be called from
        scheduler.
        """
        caplog.set_level(logging.INFO)

        job = schedule_reminders_upcoming_tasks()
        mock_job_scheduler.assert_called_once()

        # check result
        assert caplog.messages[0] == (f'Task {job.id} generate_reminders_upcoming_tasks scheduled')

    def test_schedule_reminder_upcoming_task_after_date_change(self):
        pass

    def test_no_adviser_subscription_for_adivser(self):
        pass

    def test_migration_forwards_func(self):
        # Import migration file dynamically as it start with a number
        module = import_module('datahub.task.migrations.0005_task_reminder_date')

        task = TaskFactory(reminder_days=7, due_date=datetime.date.today())
        module.forwards_func(apps, None)

        assert task.reminder_date == task.due_date - datetime.timedelta(days=task.reminder_days)
