import datetime
import logging
from unittest import mock
from unittest.mock import ANY
from uuid import uuid4

import pytest

from django.db.models.signals import m2m_changed, post_delete, post_save, pre_delete, pre_save
from django.test.utils import override_settings
from django.utils import timezone


from datahub.feature_flag.test.factories import UserFeatureFlagFactory
from datahub.reminder import ADVISER_TASKS_USER_FEATURE_FLAG_NAME
from datahub.reminder.models import (
    TaskAssignedToMeFromOthersReminder,
    TaskAssignedToMeFromOthersSubscription,
    TaskCompletedReminder,
    TaskCompletedSubscription,
    UpcomingTaskReminder,
    UpcomingTaskReminderSubscription,
)
from datahub.reminder.test.factories import (
    TaskAssignedToMeFromOthersReminderFactory,
    TaskCompletedReminderFactory,
    UpcomingTaskReminderFactory,
)
from datahub.task.emails import (
    TaskAssignedToOthersEmailTemplate,
    TaskCompletedEmailTemplate,
    UpcomingTaskEmailTemplate,
)

from datahub.task.tasks import (
    create_task_completed_subscription,
    create_task_reminder_subscription_task,
    create_upcoming_task_reminder,
    generate_reminders_upcoming_tasks,
    notify_adviser_added_to_task,
    notify_adviser_completed_task,
    schedule_reminders_upcoming_tasks,
    update_task_assigned_to_me_from_others_email_status,
    update_task_completed_email_status,
    update_task_reminder_email_status,
)
from datahub.task.test.factories import AdviserFactory, TaskFactory


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


def task_factory_due_on_date(days=1, advisers=None, due_date=None):
    if not advisers:
        advisers = [AdviserFactory()]
    if not due_date:
        due_date = datetime.date.today()
    if advisers:
        [create_task_reminder_subscription_task(adviser.id) for adviser in advisers]
    return TaskFactory(
        due_date=due_date + datetime.timedelta(days=days),
        reminder_days=days,
        advisers=advisers,
    )


def mock_notify_adviser_task_due_email_call(
    task_due,
    matching_adviser,
    template_id,
):
    reminder = UpcomingTaskReminderFactory(
        adviser=matching_adviser,
        task=task_due,
        event=f'{task_due.reminder_days} days left to task due',
    )
    reminder.id = ANY
    reminder.pk = ANY

    return mock.call(
        adviser=matching_adviser,
        template_identifier=template_id,
        context=UpcomingTaskEmailTemplate(task_due).get_context(),
        update_task=update_task_reminder_email_status,
        reminders=[reminder],
    )


@pytest.fixture()
def mute_signals(request):
    signals = [pre_save, post_save, pre_delete, post_delete, m2m_changed]
    restore = {}
    for signal in signals:
        restore[signal] = signal.receivers
        signal.receivers = []

    def restore_signals():
        for signal, receivers in restore.items():
            signal.sender_receivers_cache.clear()
            signal.receivers = receivers

    request.addfinalizer(restore_signals)


@pytest.mark.django_db
@pytest.mark.usefixtures('mute_signals')
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
        task_factory_due_on_date(1, advisers=[adviser])

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
        tasks = TaskFactory.create_batch(4)
        tasks_due = []
        matching_advisers = AdviserFactory.create_batch(3)
        matching_advisers = [
            add_user_feature_flag(adviser_tasks_user_feature_flag, adviser)
            for adviser in matching_advisers
        ]
        tasks_due.append(
            task_factory_due_on_date(
                1,
                advisers=[matching_advisers[0]],
            ),
        )
        tasks_due.append(
            task_factory_due_on_date(
                7,
                advisers=[matching_advisers[1]],
            ),
        )
        tasks_due.append(task_factory_due_on_date(30, advisers=matching_advisers))

        template_id = str(uuid4())
        with override_settings(
            TASK_REMINDER_EMAIL_TEMPLATE_ID=template_id,
        ):
            tasks = generate_reminders_upcoming_tasks()

            assert tasks.count() == 3

        mock_notify_adviser_by_rq_email.assert_has_calls(
            [
                mock_notify_adviser_task_due_email_call(
                    tasks_due[0],
                    matching_advisers[0],
                    template_id,
                ),
                mock_notify_adviser_task_due_email_call(
                    tasks_due[1],
                    matching_advisers[1],
                    template_id,
                ),
                mock_notify_adviser_task_due_email_call(
                    tasks_due[2],
                    matching_advisers[0],
                    template_id,
                ),
                mock_notify_adviser_task_due_email_call(
                    tasks_due[2],
                    matching_advisers[1],
                    template_id,
                ),
                mock_notify_adviser_task_due_email_call(
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
        task_due = task_factory_due_on_date(1, advisers=matching_advisers)
        subscription = UpcomingTaskReminderSubscription.objects.filter(
            adviser=matching_advisers[1],
        ).first()
        subscription.email_reminders_enabled = False
        subscription.save()
        mock_notify_adviser_by_rq_email.reset_mock()

        template_id = str(uuid4())
        with override_settings(
            TASK_REMINDER_EMAIL_TEMPLATE_ID=template_id,
        ):
            generate_reminders_upcoming_tasks()

        mock_notify_adviser_by_rq_email.assert_has_calls(
            [
                mock_notify_adviser_task_due_email_call(
                    task_due,
                    matching_advisers[0],
                    template_id,
                ),
            ],
        )
        mock_notify_adviser_by_rq_email.assert_called_once()

    def test_notification_received_but_no_email_sent_to_adviser_when_email_subscription_disabled(
        self,
        adviser_tasks_user_feature_flag,
        mock_notify_adviser_by_rq_email,
        mock_statsd,
        caplog,
    ):
        caplog.set_level(logging.INFO)

        # Create two advisers one with and one without an task reminder email subscription
        adviser = AdviserFactory()
        add_user_feature_flag(adviser_tasks_user_feature_flag, adviser)
        task_due = task_factory_due_on_date(1, advisers=[adviser])

        create_upcoming_task_reminder(task_due, adviser, False, timezone.now())

        reminder = UpcomingTaskReminder.objects.filter(adviser=adviser, task=task_due).first()
        assert reminder is not None

        mock_notify_adviser_by_rq_email.assert_not_called()

        assert caplog.messages == [
            f'No email for UpcomingTaskReminder with id {reminder.id} sent to adviser '
            f'{adviser.id} for task {task_due.id}, as email reminders are turned off in their '
            'subscription',
        ]

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

        task_due = task_factory_due_on_date(1, advisers=matching_advisers)
        subscription = UpcomingTaskReminderSubscription.objects.filter(
            adviser=matching_advisers[1],
        ).first()
        subscription.email_reminders_enabled = False
        subscription.save()
        mock_notify_adviser_by_rq_email.reset_mock()

        template_id = str(uuid4())
        with override_settings(
            TASK_REMINDER_EMAIL_TEMPLATE_ID=template_id,
        ):
            generate_reminders_upcoming_tasks()

        mock_notify_adviser_by_rq_email.assert_has_calls(
            [
                mock_notify_adviser_task_due_email_call(
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
        task_due = task_factory_due_on_date(1, advisers=[adviser])
        mock_notify_adviser_by_rq_email.reset_mock()

        template_id = str(uuid4())
        with override_settings(
            TASK_REMINDER_EMAIL_TEMPLATE_ID=template_id,
        ):
            generate_reminders_upcoming_tasks()
            generate_reminders_upcoming_tasks()

        mock_notify_adviser_by_rq_email.assert_has_calls(
            [
                mock_notify_adviser_task_due_email_call(
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

    def test_subscription_is_created_when_subscription_does_not_exist_for_adviser(self):
        adviser = AdviserFactory()
        TaskFactory(advisers=[adviser])

        create_task_reminder_subscription_task(adviser.id)

        subscription = UpcomingTaskReminderSubscription.objects.filter(adviser=adviser).first()
        assert subscription is not None


def mock_notify_adviser_task_assigned_from_others_call(task, adviser, template_id):
    reminder = TaskAssignedToMeFromOthersReminderFactory(
        adviser=adviser,
        task=task,
        event=f'{task} assigned to me by {task.modified_by.name}',
    )
    reminder.id = ANY
    reminder.pk = ANY

    return mock.call(
        adviser=adviser,
        template_identifier=template_id,
        context=TaskAssignedToOthersEmailTemplate(task).get_context(),
        update_task=update_task_assigned_to_me_from_others_email_status,
        reminders=[reminder],
    )


def mock_notify_adviser_task_completed_call(task, adviser, template_id):
    reminder = TaskCompletedReminderFactory(
        adviser=adviser,
        task=task,
        event=f'{task} completed by {task.modified_by.name}',
    )
    reminder.id = ANY
    reminder.pk = ANY

    return mock.call(
        adviser=adviser,
        template_identifier=template_id,
        context=TaskCompletedEmailTemplate(task).get_context(),
        update_task=update_task_completed_email_status,
        reminders=[reminder],
    )


@pytest.mark.django_db
@pytest.mark.usefixtures('mute_signals')
class TestTasksAssignedToMeFromOthers:
    def test_creation_of_multiple_adviser_subscriptions_on_task_creation(self):
        TaskFactory()

        advisers = AdviserFactory.create_batch(3)

        task1 = TaskFactory(advisers=[advisers[0], advisers[1]])
        notify_adviser_added_to_task(task1, advisers[0].id)
        notify_adviser_added_to_task(task1, advisers[1].id)

        subscriptions = TaskAssignedToMeFromOthersSubscription.objects.filter(
            adviser__in=[advisers[0], advisers[1]],
        )

        assert subscriptions.count() == 2

        task2 = TaskFactory(advisers=advisers)
        notify_adviser_added_to_task(task2, advisers[2].id)
        subscriptions = TaskAssignedToMeFromOthersSubscription.objects.filter(
            adviser__in=advisers,
        )

        assert subscriptions.count() == 3

    def test_notification_created_when_single_adviser_assigned_to_task(self):
        adviser = AdviserFactory()
        task1 = TaskFactory(advisers=[adviser])
        notify_adviser_added_to_task(task1, adviser.id)
        reminders = TaskAssignedToMeFromOthersReminder.objects.filter(adviser=adviser)

        assert reminders.exists()

        task2 = TaskFactory(advisers=[adviser])
        notify_adviser_added_to_task(task2, adviser.id)
        reminders = TaskAssignedToMeFromOthersReminder.objects.filter(adviser=adviser)

        assert reminders.count() == 2

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
            TASK_REMINDER_EMAIL_TEMPLATE_ID=template_id,
        ):
            task = TaskFactory(advisers=[adviser], due_date=datetime.date.today())

            notify_adviser_added_to_task(
                task,
                adviser.id,
            )

            mock_notify_adviser_by_rq_email.assert_has_calls(
                [
                    mock_notify_adviser_task_assigned_from_others_call(
                        task,
                        adviser,
                        template_id,
                    ),
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
            TASK_REMINDER_EMAIL_TEMPLATE_ID=template_id,
        ):
            task = TaskFactory(advisers=[adviser], due_date=datetime.date.today())

            notify_adviser_added_to_task(
                task,
                adviser.id,
            )

            mock_notify_adviser_by_rq_email.assert_has_calls(
                [
                    mock_notify_adviser_task_assigned_from_others_call(
                        task,
                        adviser,
                        template_id,
                    ),
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
            TASK_REMINDER_EMAIL_TEMPLATE_ID=template_id,
        ):
            task = TaskFactory(advisers=[adviser], due_date=datetime.date.today())

            notify_adviser_added_to_task(
                task,
                adviser.id,
            )

            mock_notify_adviser_by_rq_email.assert_has_calls(
                [
                    mock_notify_adviser_task_assigned_from_others_call(
                        task,
                        adviser,
                        template_id,
                    ),
                ],
            )

    def test_notification_received_but_no_email_sent_to_adviser_when_email_subscription_disabled(
        self,
        adviser_tasks_user_feature_flag,
        caplog,
    ):
        caplog.set_level(logging.INFO)

        # create a task and assign an adviser
        adviser = AdviserFactory()
        adviser = add_user_feature_flag(adviser_tasks_user_feature_flag, adviser)
        TaskAssignedToMeFromOthersSubscription.objects.create(
            adviser=adviser,
            email_reminders_enabled=False,
        )
        task = TaskFactory(advisers=[adviser])

        response = notify_adviser_added_to_task(task, adviser.id)
        reminder = TaskAssignedToMeFromOthersReminder.objects.filter(
            adviser=adviser,
            task=task,
        ).first()
        assert reminder is not None

        assert response is None

        assert caplog.messages == [
            f'No email for TaskAssignedToMeFromOthersReminder with id {reminder.id} sent to '
            f'adviser {adviser.id} for task {task.id}, as email reminders are turned off in their '
            'subscription',
        ]

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


@pytest.mark.django_db
@pytest.mark.usefixtures('mute_signals')
class TestTaskCompleted:
    def test_creation_of_multiple_adviser_subscriptions_on_task_creation(self):
        TaskFactory()

        advisers = AdviserFactory.create_batch(3)

        TaskFactory(advisers=[advisers[0], advisers[1]])
        create_task_completed_subscription(advisers[0].id)
        create_task_completed_subscription(advisers[1].id)

        subscriptions = TaskCompletedSubscription.objects.filter(
            adviser__in=[advisers[0], advisers[1]],
        )

        assert subscriptions.count() == 2

        TaskFactory(advisers=advisers)
        create_task_completed_subscription(advisers[2].id)
        subscriptions = TaskCompletedSubscription.objects.filter(
            adviser__in=advisers,
        )

        assert subscriptions.count() == 3

    def test_no_reminders_created_when_a_task_is_created(self):
        task = TaskFactory()
        notify_adviser_completed_task(task, False)
        assert TaskCompletedReminder.objects.exists() is False

    def test_no_reminders_created_when_a_task_is_not_archived(self):
        task = TaskFactory(archived=False)
        notify_adviser_completed_task(task, True)
        assert TaskCompletedReminder.objects.exists() is False

    def test_no_reminders_created_when_adviser_that_completes_task_is_the_only_adviser(
        self,
    ):
        adviser = AdviserFactory()
        task = TaskFactory(archived=True, modified_by=adviser, advisers=[adviser])

        notify_adviser_completed_task(task, False)

        assert TaskCompletedReminder.objects.exists() is False

    def test_adviser_that_completes_task_does_not_receive_notification_about_that_task_completion(
        self,
    ):
        modified_by_adviser = AdviserFactory()
        adviser = AdviserFactory()
        task = TaskFactory(
            archived=True,
            modified_by=modified_by_adviser,
            advisers=[
                modified_by_adviser,
                adviser,
            ],
        )

        notify_adviser_completed_task(task, False)

        assert TaskCompletedReminder.objects.filter(adviser=modified_by_adviser).exists() is False
        assert TaskCompletedReminder.objects.filter(adviser=adviser).exists() is True

    def test_adviser_that_has_received_notification_for_this_task_does_not_receive_another(
        self,
    ):
        adviser_existing_notification = AdviserFactory()
        adviser_no_notification = AdviserFactory()
        task = TaskFactory(
            archived=True,
            advisers=[
                adviser_existing_notification,
                adviser_no_notification,
            ],
        )

        TaskCompletedReminder.objects.create(
            task=task,
            adviser=adviser_existing_notification,
            event='Test duplicates not received',
        )

        notify_adviser_completed_task(task, False)

        assert (
            TaskCompletedReminder.objects.filter(adviser=adviser_existing_notification).count()
            == 1
        )

        assert TaskCompletedReminder.objects.filter(adviser=adviser_no_notification).count() == 1

    def test_notification_received_but_no_email_sent_to_adviser_without_subscription(
        self,
        mock_notify_adviser_by_rq_email,
    ):
        adviser = AdviserFactory()
        task = TaskFactory(
            archived=True,
            advisers=[
                adviser,
            ],
        )

        notify_adviser_completed_task(task, False)

        assert TaskCompletedReminder.objects.filter(adviser=adviser).count() == 1
        mock_notify_adviser_by_rq_email.assert_not_called()

    def test_notification_received_but_no_email_sent_to_adviser_when_email_subscription_disabled(
        self,
        mock_notify_adviser_by_rq_email,
        caplog,
    ):
        caplog.set_level(logging.INFO)

        adviser = AdviserFactory()
        task = TaskFactory(
            archived=True,
            advisers=[
                adviser,
            ],
        )

        TaskCompletedSubscription.objects.create(
            adviser_id=adviser.id,
            email_reminders_enabled=False,
        )

        notify_adviser_completed_task(task, False)

        reminder = TaskCompletedReminder.objects.filter(adviser=adviser).first()
        assert reminder is not None

        mock_notify_adviser_by_rq_email.assert_not_called()
        assert caplog.messages == [
            f'No email for TaskCompletedReminder with id {reminder.id} sent to adviser '
            f'{adviser.id} for task {task.id}, as email reminders are turned off in their '
            'subscription',
        ]

    def test_notification_received_but_no_email_sent_to_adviser_with_email_on_with_no_feature_flag(
        self,
        mock_notify_adviser_by_rq_email,
    ):
        adviser = AdviserFactory()
        task = TaskFactory(
            archived=True,
            advisers=[
                adviser,
            ],
        )

        create_task_completed_subscription(adviser_id=adviser.id)

        notify_adviser_completed_task(task, False)

        assert TaskCompletedReminder.objects.filter(adviser=adviser).count() == 1
        mock_notify_adviser_by_rq_email.assert_not_called()

    def test_notification_received_but_no_email_for_adviser_with_email_off_with_feature_flag_on(
        self,
        adviser_tasks_user_feature_flag,
        mock_notify_adviser_by_rq_email,
    ):
        adviser = AdviserFactory()
        add_user_feature_flag(adviser_tasks_user_feature_flag, adviser)
        task = TaskFactory(
            archived=True,
            advisers=[
                adviser,
            ],
        )

        TaskCompletedSubscription.objects.create(
            adviser_id=adviser.id,
            email_reminders_enabled=False,
        )

        notify_adviser_completed_task(task, False)

        assert TaskCompletedReminder.objects.filter(adviser=adviser).count() == 1
        mock_notify_adviser_by_rq_email.assert_not_called()

    def test_email_sent_for_adviser_with_email_on_with_feature_flag_on(
        self,
        adviser_tasks_user_feature_flag,
        mock_notify_adviser_by_rq_email,
    ):
        adviser = AdviserFactory()
        add_user_feature_flag(adviser_tasks_user_feature_flag, adviser)
        create_task_completed_subscription(adviser.id)

        template_id = str(uuid4())
        with override_settings(
            TASK_REMINDER_EMAIL_TEMPLATE_ID=template_id,
        ):
            task = TaskFactory(
                advisers=[adviser],
                archived=True,
            )

            notify_adviser_completed_task(
                task,
                False,
            )

            mock_notify_adviser_by_rq_email.assert_has_calls(
                [
                    mock_notify_adviser_task_completed_call(
                        task,
                        adviser,
                        template_id,
                    ),
                ],
            )

    def test_task_completed_assigns_email_notification_id_to_all_reminders(
        self,
    ):
        """
        Test it updates reminder data with the connected email notification information.
        """
        task = TaskFactory()
        reminder_number = 3
        notification_id = str(uuid4())
        reminders = TaskCompletedReminderFactory.create_batch(
            reminder_number,
            task_id=task.id,
        )

        update_task_completed_email_status(
            notification_id,
            [reminder.id for reminder in reminders],
        )

        linked_reminders = TaskCompletedReminder.objects.filter(
            email_notification_id=notification_id,
        )
        assert linked_reminders.count() == (reminder_number)
