import functools
from unittest.mock import call, patch

import pytest

from django.db.models.signals import m2m_changed
from factory.django import mute_signals

from datahub.company.test.factories import AdviserFactory
from datahub.task.signals import set_task_subscriptions_and_schedule_notifications
from datahub.task.test.factories import TaskFactory


def patch_all_task_subscription_functions(f):
    @patch('datahub.task.signals.schedule_create_task_reminder_subscription_task')
    @patch(
        'datahub.task.signals.schedule_create_task_assigned_to_me_from_others_subscription_task',
    )
    @patch(
        'datahub.task.signals.schedule_create_task_overdue_subscription_task',
    )
    @patch('datahub.task.signals.schedule_create_task_completed_subscription_task')
    @functools.wraps(f)
    def functor(*args, **kwargs):
        return f(*args, **kwargs)

    return functor


@pytest.mark.django_db
class TestTaskAdviserChangedSubscriptions:
    @patch_all_task_subscription_functions
    def test_schedule_functions_called_for_each_adviser(
        self,
        schedule_create_task_completed_subscription_task,
        schedule_create_task_overdue_subscription_task,
        schedule_create_task_assigned_to_me_from_others_subscription_task,
        schedule_create_task_reminder_subscription_task,
    ):
        advisers = AdviserFactory.create_batch(2)
        task = TaskFactory(advisers=advisers)

        schedule_create_task_reminder_subscription_task.assert_has_calls(
            [call(adviser.id) for adviser in advisers],
            any_order=True,
        )
        schedule_create_task_assigned_to_me_from_others_subscription_task.assert_has_calls(
            [call(task, adviser.id) for adviser in advisers],
            any_order=True,
        )
        schedule_create_task_overdue_subscription_task.assert_has_calls(
            [call(adviser.id) for adviser in advisers],
            any_order=True,
        )
        schedule_create_task_completed_subscription_task.assert_has_calls(
            [call(adviser.id) for adviser in advisers],
            any_order=True,
        )

    @patch_all_task_subscription_functions
    def test_pk_set_to_none_does_not_trigger_scheduled_tasks(
        self,
        schedule_create_task_completed_subscription_task,
        schedule_create_task_overdue_subscription_task,
        schedule_create_task_assigned_to_me_from_others_subscription_task,
        schedule_create_task_reminder_subscription_task,
    ):
        myargs = {'action': 'post_add', 'instance': 'a task'}
        set_task_subscriptions_and_schedule_notifications(sender=None, **myargs)

        schedule_create_task_reminder_subscription_task.assert_not_called()
        schedule_create_task_assigned_to_me_from_others_subscription_task.assert_not_called()
        schedule_create_task_overdue_subscription_task.assert_not_called()
        schedule_create_task_completed_subscription_task.assert_not_called()

    @patch_all_task_subscription_functions
    def test_instance_set_to_none_does_not_trigger_scheduled_tasks(
        self,
        schedule_create_task_completed_subscription_task,
        schedule_create_task_overdue_subscription_task,
        schedule_create_task_assigned_to_me_from_others_subscription_task,
        schedule_create_task_reminder_subscription_task,
    ):
        myargs = {'action': 'post_add', 'pk_set': 'some advisers'}
        set_task_subscriptions_and_schedule_notifications(sender=None, **myargs)

        schedule_create_task_reminder_subscription_task.assert_not_called()
        schedule_create_task_assigned_to_me_from_others_subscription_task.assert_not_called()
        schedule_create_task_overdue_subscription_task.assert_not_called()
        schedule_create_task_completed_subscription_task.assert_not_called()

    @patch_all_task_subscription_functions
    def test_removing_adviser_does_not_trigger_scheduled_tasks(
        self,
        schedule_create_task_completed_subscription_task,
        schedule_create_task_overdue_subscription_task,
        schedule_create_task_assigned_to_me_from_others_subscription_task,
        schedule_create_task_reminder_subscription_task,
    ):
        advisers = AdviserFactory.create_batch(2)
        task = TaskFactory(advisers=advisers)

        schedule_create_task_reminder_subscription_task.reset_mock()
        schedule_create_task_assigned_to_me_from_others_subscription_task.reset_mock()
        schedule_create_task_overdue_subscription_task.reset_mock()
        schedule_create_task_completed_subscription_task.reset_mock()

        task.advisers.remove(advisers[0])

        schedule_create_task_reminder_subscription_task.assert_not_called()
        schedule_create_task_assigned_to_me_from_others_subscription_task.assert_not_called()
        schedule_create_task_overdue_subscription_task.assert_not_called()
        schedule_create_task_completed_subscription_task.assert_not_called()


@pytest.mark.django_db
class TestTaskAdviserCompletedSubscriptions:
    @mute_signals(m2m_changed)
    @patch('datahub.task.signals.schedule_notify_advisers_task_completed')
    def test_creating_task_triggers_notify_adviser_completed_scheduled_task(
        self,
        schedule_notify_advisers_task_completed,
    ):
        task = TaskFactory(advisers=[AdviserFactory()])

        schedule_notify_advisers_task_completed.assert_has_calls(
            [
                call(task, True),
                call(task, False),
            ],
        )

    @mute_signals(m2m_changed)
    @patch('datahub.task.signals.schedule_notify_advisers_task_completed')
    def test_modifying_task_triggers_notify_adviser_completed_scheduled_task(
        self,
        schedule_notify_advisers_task_completed,
    ):
        task = TaskFactory(archived=False)
        task.archived = True
        task.save()

        schedule_notify_advisers_task_completed.assert_has_calls(
            [
                call(task, True),
                call(task, False),
                call(task, False),
            ],
        )
