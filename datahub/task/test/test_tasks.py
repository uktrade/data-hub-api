import datetime
import logging
from importlib import import_module
from unittest import mock
from unittest.mock import ANY
from uuid import uuid4


import pytest


from django.apps import apps
from django.test.utils import override_settings

from datahub.feature_flag.test.factories import UserFeatureFlagFactory
from datahub.reminder import ADVISER_TASKS_USER_FEATURE_FLAG_NAME
from datahub.reminder.models import (
    TaskAssignedToMeFromOthersReminder,
    TaskAssignedToMeFromOthersSubscription,
    UpcomingTaskReminder,
    UpcomingTaskReminderSubscription,
)
from datahub.reminder.test.factories import (
    TaskAssignedToMeFromOthersReminderFactory,
    UpcomingTaskReminderFactory,
)

from datahub.task.tasks import (
    generate_reminders_upcoming_tasks,
    notify_adviser_added_to_task,
    schedule_reminders_upcoming_tasks,
    update_task_assigned_to_me_from_others_email_status,
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


def investment_project_factory_due_on_date(days=1, advisers=None, due_date=None):
    if not advisers:
        advisers = [AdviserFactory()]
    if not due_date:
        due_date = datetime.date.today()
    return InvestmentProjectTaskFactory(
        task=TaskFactory(
            due_date=due_date + datetime.timedelta(days=days),
            reminder_days=days,
            advisers=advisers,
        ),
    )


def mock_notify_adviser_investment_project_task_due_email_call(
    investment_project_task_due,
    matching_adviser,
    template_id,
):
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
        investment_project_factory_due_on_date(1, advisers=[adviser])

        caplog.set_level(logging.INFO, logger='datahub.task.tasks')

        mock_advisory_lock = mock.MagicMock()
        mock_advisory_lock.return_value.__enter__.return_value = lock_acquired
        monkeypatch.setattr(
            'datahub.task.tasks.advisory_lock',
            mock_advisory_lock,
        )
        mock_notify_adviser_by_rq_email.reset_mock()

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
        tasks_due.append(
            investment_project_factory_due_on_date(
                1,
                advisers=[matching_advisers[0]],
            ),
        )
        tasks_due.append(
            investment_project_factory_due_on_date(
                7,
                advisers=[matching_advisers[1]],
            ),
        )
        tasks_due.append(investment_project_factory_due_on_date(30, advisers=matching_advisers))

        template_id = str(uuid4())
        with override_settings(
            TASK_REMINDER_STATUS_TEMPLATE_ID=template_id,
        ):
            tasks = generate_reminders_upcoming_tasks()

            assert tasks.count() == 3

        mock_notify_adviser_by_rq_email.assert_has_calls(
            [
                mock_notify_adviser_investment_project_task_due_email_call(
                    tasks_due[0],
                    matching_advisers[0],
                    template_id,
                ),
                mock_notify_adviser_investment_project_task_due_email_call(
                    tasks_due[1],
                    matching_advisers[1],
                    template_id,
                ),
                mock_notify_adviser_investment_project_task_due_email_call(
                    tasks_due[2],
                    matching_advisers[0],
                    template_id,
                ),
                mock_notify_adviser_investment_project_task_due_email_call(
                    tasks_due[2],
                    matching_advisers[1],
                    template_id,
                ),
                mock_notify_adviser_investment_project_task_due_email_call(
                    tasks_due[2],
                    matching_advisers[2],
                    template_id,
                ),
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
        task_due = investment_project_factory_due_on_date(1, advisers=matching_advisers)
        subscription = UpcomingTaskReminderSubscription.objects.filter(
            adviser=matching_advisers[1],
        ).first()
        subscription.email_reminders_enabled = False
        subscription.save()
        mock_notify_adviser_by_rq_email.reset_mock()

        template_id = str(uuid4())
        with override_settings(
            TASK_REMINDER_STATUS_TEMPLATE_ID=template_id,
        ):
            generate_reminders_upcoming_tasks()

        mock_notify_adviser_by_rq_email.assert_has_calls(
            [
                mock_notify_adviser_investment_project_task_due_email_call(
                    task_due,
                    matching_advisers[0],
                    template_id,
                ),
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

        task_due = investment_project_factory_due_on_date(1, advisers=matching_advisers)
        subscription = UpcomingTaskReminderSubscription.objects.filter(
            adviser=matching_advisers[1],
        ).first()
        subscription.email_reminders_enabled = False
        subscription.save()
        mock_notify_adviser_by_rq_email.reset_mock()

        template_id = str(uuid4())
        with override_settings(
            TASK_REMINDER_STATUS_TEMPLATE_ID=template_id,
        ):
            generate_reminders_upcoming_tasks()

        mock_notify_adviser_by_rq_email.assert_has_calls(
            [
                mock_notify_adviser_investment_project_task_due_email_call(
                    task_due,
                    matching_advisers[0],
                    template_id,
                ),
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
        task_due = investment_project_factory_due_on_date(1, advisers=[adviser])
        mock_notify_adviser_by_rq_email.reset_mock()

        template_id = str(uuid4())
        with override_settings(
            TASK_REMINDER_STATUS_TEMPLATE_ID=template_id,
        ):
            generate_reminders_upcoming_tasks()
            generate_reminders_upcoming_tasks()

        mock_notify_adviser_by_rq_email.assert_has_calls(
            [
                mock_notify_adviser_investment_project_task_due_email_call(
                    task_due,
                    adviser,
                    template_id,
                ),
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

    def test_migration_forwards_func(self):
        # Import migration file dynamically as it start with a number
        module = import_module('datahub.task.migrations.0005_task_reminder_date')

        task = TaskFactory(reminder_days=7, due_date=datetime.date.today())
        module.forwards_func(apps, None)

        assert task.reminder_date == task.due_date - datetime.timedelta(days=task.reminder_days)


def mock_notify_adviser_task_assigned_from_others_call(task, adviser, template_id):
    reminder = TaskAssignedToMeFromOthersReminderFactory(
        adviser=adviser,
        task=task,
        event=f'{task} assigned to me by {task.modified_by.name}',
    )
    reminder.id = ANY
    reminder.pk = ANY
    print('******', task)
    print('******', task.get_company())
    print('******', task.get_company().name)
    return mock.call(
        adviser=adviser,
        template_identifier=template_id,
        context={
            'task_title': task.title,
            'modified_by': task.modified_by.name,
            'company_name': task.get_company().name,
            'task_due_date': task.due_date.strftime('%-d %B %Y') if task.due_date else None,
            'task_url': task.get_absolute_url(),
        },
        update_task=update_task_assigned_to_me_from_others_email_status,
        reminders=[reminder],
    )


@pytest.mark.django_db
class TestTasksAssignedToMeFromOthers:
    def test_creation_of_adviser_subscription_on_task_creation_where_adviser_has_no_subscription(
        self,
    ):
        adviser1 = AdviserFactory()
        AdviserFactory()
        TaskFactory(advisers=[adviser1])
        subscriptions = TaskAssignedToMeFromOthersSubscription.objects.filter(adviser=adviser1)
        assert subscriptions.count() == 1

    def test_creation_of_multiple_adviser_subscriptions_on_task_creation(self):
        TaskFactory()
        adviser1 = AdviserFactory()
        adviser2 = AdviserFactory()
        AdviserFactory()
        AdviserFactory()
        TaskFactory(advisers=[adviser1, adviser2])
        subscriptions = TaskAssignedToMeFromOthersSubscription.objects.filter(
            adviser__in=[adviser1, adviser2],
        )

        assert subscriptions.count() == 2

        adviser3 = AdviserFactory()
        TaskFactory(advisers=[adviser1, adviser2, adviser3])
        subscriptions = TaskAssignedToMeFromOthersSubscription.objects.filter(
            adviser__in=[adviser1, adviser2, adviser3],
        )

        assert subscriptions.count() == 3

    def test_removal_of_adviser_from_task_that_subscription_remains(self):
        TaskFactory()
        adviser1 = AdviserFactory()
        adviser2 = AdviserFactory()
        AdviserFactory()
        AdviserFactory()
        TaskFactory(advisers=[adviser1, adviser2])
        subscriptions = TaskAssignedToMeFromOthersSubscription.objects.filter(
            adviser__in=[adviser1, adviser2],
        )

        assert subscriptions.count() == 2

        TaskFactory(advisers=[adviser1])
        subscriptions = TaskAssignedToMeFromOthersSubscription.objects.filter(
            adviser__in=[adviser1, adviser2],
        )

        assert subscriptions.count() == 2

    def test_notification_created_when_single_adviser_assigned_to_task(self):
        adviser = AdviserFactory()
        TaskFactory(advisers=[adviser])
        reminders = TaskAssignedToMeFromOthersReminder.objects.filter(adviser=adviser)

        assert reminders.count() == 1

        TaskFactory(advisers=[adviser])
        reminders = TaskAssignedToMeFromOthersReminder.objects.filter(adviser=adviser)

        assert reminders.count() == 2

    def test_notification_not_sent_when_single_adviser_removed_from_task(self):
        # create a single task and assign to an adviser
        adviser1 = AdviserFactory()
        adviser2 = AdviserFactory()
        task = TaskFactory(advisers=[adviser1, adviser2])
        reminders = TaskAssignedToMeFromOthersReminder.objects.filter(adviser=adviser1)

        assert reminders.count() == 1

        # remove the adviser from the task
        task.advisers.remove(adviser1)
        reminders_adviser1 = TaskAssignedToMeFromOthersReminder.objects.filter(adviser=adviser1)
        reminders_adviser2 = TaskAssignedToMeFromOthersReminder.objects.filter(adviser=adviser2)

        assert reminders_adviser1.count() == 1
        assert reminders_adviser2.count() == 1

    def test_email_sent_for_adviser_with_no_subscription_set(
        self,
        adviser_tasks_user_feature_flag,
        mock_notify_adviser_by_rq_email,
    ):
        # create a task and assign an adviser
        adviser = AdviserFactory()
        adviser = add_user_feature_flag(adviser_tasks_user_feature_flag, adviser)

        template_id = str(uuid4())
        with override_settings(
            TASK_NOTIFICATION_FROM_OTHERS_TEMPLATE_ID=template_id,
        ):
            task = TaskFactory(advisers=[adviser], due_date=datetime.date.today())
            mock_notify_adviser_by_rq_email.assert_has_calls(
                [
                    mock_notify_adviser_task_assigned_from_others_call(task, adviser, template_id),
                ],
            )

    def test_email_sent_for_adviser_with_no_subscription_set_and_no_due_date(
        self,
        adviser_tasks_user_feature_flag,
        mock_notify_adviser_by_rq_email,
    ):
        # create a task and assign an adviser
        adviser = AdviserFactory()
        adviser = add_user_feature_flag(adviser_tasks_user_feature_flag, adviser)

        template_id = str(uuid4())
        with override_settings(
            TASK_NOTIFICATION_FROM_OTHERS_TEMPLATE_ID=template_id,
        ):
            task = TaskFactory(advisers=[adviser], due_date=None)
            mock_notify_adviser_by_rq_email.assert_has_calls(
                [
                    mock_notify_adviser_task_assigned_from_others_call(task, adviser, template_id),
                ],
            )

    def test_email_sent_for_adviser_with_existing_subscription_and_notify_by_email_true(
        self,
        adviser_tasks_user_feature_flag,
        mock_notify_adviser_by_rq_email,
    ):
        adviser = AdviserFactory()
        adviser = add_user_feature_flag(adviser_tasks_user_feature_flag, adviser)
        TaskAssignedToMeFromOthersSubscription.objects.create(
            adviser=adviser,
            email_reminders_enabled=True,
        )
        template_id = str(uuid4())
        with override_settings(
            TASK_NOTIFICATION_FROM_OTHERS_TEMPLATE_ID=template_id,
        ):
            investment_project_task = InvestmentProjectTaskFactory(
                task=TaskFactory(advisers=[adviser], due_date=datetime.date.today())
            )
            # task = TaskFactory(advisers=[adviser], due_date=datetime.date.today())
            mock_notify_adviser_by_rq_email.assert_has_calls(
                [
                    mock_notify_adviser_task_assigned_from_others_call(
                        investment_project_task.task, adviser, template_id
                    ),
                ],
            )

    def test_task_assigned_to_me_from_others_email_not_sent_if_email_reminders_enabled_not_enabled(
        self,
        adviser_tasks_user_feature_flag,
    ):
        # create a task and assign an adviser
        adviser = AdviserFactory()
        adviser = add_user_feature_flag(adviser_tasks_user_feature_flag, adviser)
        TaskAssignedToMeFromOthersSubscription.objects.create(
            adviser=adviser,
            email_reminders_enabled=False,
        )
        task = TaskFactory(advisers=[adviser])

        response = notify_adviser_added_to_task(task, adviser.id)

        assert response is None

    def test_task_assigned_to_me_from_others_email_not_sent_if_feature_flag_not_enabled(
        self,
    ):
        adviser = AdviserFactory()
        task = TaskFactory(advisers=[adviser])

        response = notify_adviser_added_to_task(task, adviser.id)

        assert response is None

    def test_task_assigned_to_me_from_others_reminder_email_status(
        self,
    ):
        """
        Test it updates reminder data with the connected email notification information.
        """
        task = TaskFactory()
        reminder_number = 3
        notification_id = str(uuid4())
        reminders = TaskAssignedToMeFromOthersReminderFactory.create_batch(
            reminder_number,
            task_id=task.id,
        )

        update_task_assigned_to_me_from_others_email_status(
            notification_id,
            [reminder.id for reminder in reminders],
        )

        task2 = TaskFactory()
        TaskAssignedToMeFromOthersReminderFactory.create_batch(2, task_id=task2.id)

        linked_reminders = TaskAssignedToMeFromOthersReminder.objects.filter(
            email_notification_id=notification_id,
        )
        assert linked_reminders.count() == (reminder_number)

    def test_task_assigned_to_me_from_others_notification_returns_if_adviser_id_not_correct(self):
        adviser = AdviserFactory()
        task = TaskFactory(advisers=[adviser])
        random_id = str(uuid4())

        response = notify_adviser_added_to_task(task, random_id)

        assert response is None
