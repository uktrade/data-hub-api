from unittest.mock import ANY, call, patch

import pytest

from datahub.company.test.factories import AdviserFactory
from datahub.task.emails import TaskCompletedEmailTemplate
from datahub.task.models import Task
from datahub.task.signals import set_task_subscriptions_and_schedule_notifications
from datahub.task.tasks import update_task_completed_email_status
from datahub.task.test.factories import TaskFactory


pytestmark = [pytest.mark.django_db, pytest.mark.enable_task_signals]


class TestTaskAdviserChangedSubscriptions:
    @patch('datahub.task.signals.schedule_advisers_added_to_task')
    def test_schedule_functions_called_for_each_adviser(
        self,
        schedule_advisers_added_to_task,
    ):
        advisers = AdviserFactory.create_batch(2)
        task = TaskFactory(advisers=advisers)
        adviser_ids = set([adviser.id for adviser in advisers])

        schedule_advisers_added_to_task.assert_has_calls(
            [
                call(
                    adviser_ids=adviser_ids,
                    task=task,
                ),
            ],
        )

    @patch('datahub.task.signals.schedule_advisers_added_to_task')
    def test_pk_set_to_none_does_not_trigger_scheduled_tasks(
        self,
        schedule_advisers_added_to_task,
    ):
        myargs = {'action': 'post_add', 'instance': 'a task'}
        set_task_subscriptions_and_schedule_notifications(sender=None, **myargs)

        schedule_advisers_added_to_task.assert_not_called()

    @patch('datahub.task.signals.schedule_advisers_added_to_task')
    def test_instance_set_to_none_does_not_trigger_scheduled_tasks(
        self,
        schedule_advisers_added_to_task,
    ):
        myargs = {'action': 'post_add', 'pk_set': 'some advisers'}
        set_task_subscriptions_and_schedule_notifications(sender=None, **myargs)

        schedule_advisers_added_to_task.assert_not_called()

    @patch('datahub.task.signals.schedule_advisers_added_to_task')
    def test_removing_adviser_does_not_trigger_scheduled_tasks(
        self,
        schedule_advisers_added_to_task,
    ):
        advisers = AdviserFactory.create_batch(2)
        task = TaskFactory(advisers=advisers)

        schedule_advisers_added_to_task.reset_mock()

        task.advisers.remove(advisers[0])

        schedule_advisers_added_to_task.assert_not_called()


class TestTaskAdviserCompletedSubscriptions:
    @patch('datahub.task.signals.schedule_notify_advisers_task_completed')
    def test_creating_and_updating_task_triggers_notify_adviser_completed_scheduled_task(
        self,
        schedule_notify_advisers_task_completed,
    ):
        """
        Note: only the triggering of the schedule is tested not the processing of it.
        """
        task = TaskFactory(advisers=[AdviserFactory()])
        task.save()

        schedule_notify_advisers_task_completed.assert_has_calls(
            [
                call(task, True),
                call(task, False),
                call(task, False),
            ],
            any_order=True,
        )

    @patch('datahub.task.tasks.send_task_email')
    def test_setting_status_complete_triggers_send_task_email(
        self,
        send_task_email,
    ):
        """
        Calling with adviser completed should result in sending of TaskCompletedReminder
        """
        adviser = AdviserFactory()
        task = TaskFactory(advisers=[adviser])
        task.status = Task.Status.COMPLETE
        task.save()

        send_task_email.assert_any_call(
            adviser=adviser,
            task=task,
            reminder=ANY,
            update_task=update_task_completed_email_status,
            email_template_class=TaskCompletedEmailTemplate,
        )


class TestTaskAmededByOthersSubscriptions:
    @patch('datahub.task.signals.schedule_notify_advisers_task_amended_by_others')
    def test_creating_task_triggers_notify_advisers_task_amended_by_others_scheduled_task(
        self,
        schedule_notify_advisers_task_amended_by_others,
    ):
        adviser = AdviserFactory()
        task = TaskFactory(advisers=[adviser])

        schedule_notify_advisers_task_amended_by_others.assert_has_calls(
            [
                call(task, True, []),
                call(task, False, [adviser.id]),
            ],
            any_order=True,
        )

    @patch('datahub.task.signals.schedule_notify_advisers_task_amended_by_others')
    def test_modifying_task_triggers_notify_advisers_task_amended_by_others_scheduled_task(
        self,
        schedule_notify_advisers_task_amended_by_others,
    ):
        adviser = AdviserFactory()
        task = TaskFactory(advisers=[adviser])
        task.save()

        schedule_notify_advisers_task_amended_by_others.assert_has_calls(
            [
                call(task, True, []),
                call(task, False, [adviser.id]),
                call(task, False, [adviser.id]),
            ],
            any_order=True,
        )
