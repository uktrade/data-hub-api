import datetime
from unittest import mock
from unittest.mock import ANY
from uuid import uuid4


import pytest

from django.test.utils import override_settings

from datahub.reminder.test.factories import UpcomingTaskReminderFactory
from datahub.task.tasks import generate_reminders_upcoming_tasks, update_task_reminder_email_status
from datahub.task.test.factories import AdviserFactory, InvestmentProjectTaskFactory, TaskFactory

# from datahub.reminder.test.test_emails import mock_notify_adviser_by_rq_email, mock_statsd


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


@pytest.mark.django_db
class TestTaskReminders:
    def test_generate_reminders_for_upcoming_tasks(
        self, mock_notify_adviser_by_rq_email, mock_statsd,
    ):
        # create a few tasks without due reminders
        # create a few tasks with due reminders
        tasks = InvestmentProjectTaskFactory.create_batch(4)
        tasks_due = []
        matching_advisers = AdviserFactory.create_batch(3)
        tasks_due.append(investment_project_factory_due_today(1, advisers=[matching_advisers[0]]))
        tasks_due.append(investment_project_factory_due_today(7, advisers=[matching_advisers[1]]))
        tasks_due.append(investment_project_factory_due_today(30, advisers=matching_advisers))
        # task_id = task.id

        # investment_project_task = InvestmentProjectTaskFactory(task=task)

        template_id = str(uuid4())
        with override_settings(
            TASK_REMINDER_STATUS_TEMPLATE_ID=template_id,
        ):
            tasks = generate_reminders_upcoming_tasks()

            assert tasks.count() == 3

        reminder = UpcomingTaskReminderFactory(
            adviser=matching_advisers[0], task=tasks_due[0].task, event='1 days left to task due',
        )
        reminder.id = ANY
        reminder.pk = ANY

        mock_notify_adviser_by_rq_email.assert_called_with(
            adviser=matching_advisers[0],
            template_identifier=template_id,
            context={
                'task_title': tasks_due[0].task.title,
                'company_name': '',
                'task_due_date': tasks_due[0].task.due_date,
                'company_contact_email_address': '',
                'task_url': '',
                'complete_task_url': '',
            },
            update_task=update_task_reminder_email_status,
            reminders=[reminder],
        )

        # actual_ids = Counter(str(adviser.pk) for adviser in matching_advisers)
        # expected_ids = Counter(result['id'] for result in response_data['results'])
        # assert actual_ids == expected_ids

        # Check tasks count is number due reminders expected
        # assert tasks.count() == 3

    def test_emails_not_send_when_email_subscription_not_enabled_by_adviser():
        pass

    def test_update_task_reminder_email_status_set():
        # Test that the update_task_reminder_email_status method is called from
        # send_task_reminder_email
        pass

    # tasks [due_date - reminder_days = today]
    #   advisers [is_active && ]
    #       upcoming_task_reminder_subscription [select email_reminder_enabled]

    #   userfeatureflag or userfeatureflag group set

    # Add reminder to DataHub reminders
    # Send email if upcoming_task_reminder_subscription.email_reminder_enabled
