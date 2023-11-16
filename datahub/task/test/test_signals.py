from unittest.mock import call, patch

import pytest

from django.db.models.signals import m2m_changed
from factory.django import mute_signals

from datahub.company.test.factories import AdviserFactory
from datahub.task.models import Task
from datahub.task.test.factories import InvestmentProjectTaskFactory, TaskFactory


@pytest.mark.django_db
class TestDeleteInvestmentProjectTask:
    @mute_signals(m2m_changed)
    def test_delete_investment_project_task__without_linked_tasks_does_nothing(self):
        task = TaskFactory()
        task_id = task.id

        investment_project_task = InvestmentProjectTaskFactory(task=task)
        task.delete()
        investment_project_task.delete()

        obj = Task.objects.filter(pk=task_id).first()
        assert obj is None

    @mute_signals(m2m_changed)
    def test_delete_investment_project_task_deletes_linked_task(self):
        task = TaskFactory()
        task_id = task.id

        investment_project_task = InvestmentProjectTaskFactory(task=task)
        investment_project_task.delete()

        obj = Task.objects.filter(pk=task_id).first()
        assert obj is None


@pytest.mark.django_db
class TestTaskAdviserChangedSubscriptions:
    @patch('datahub.task.signals.schedule_create_task_reminder_subscription_task')
    @patch(
        'datahub.task.signals.schedule_create_task_assigned_to_me_from_others_subscription_task',
    )
    @patch(
        'datahub.task.signals.schedule_create_task_overdue_subscription_task',
    )
    def test_schedule_functions_called_for_each_adviser(
        self,
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

    def test_modifications_to_task_advisers(self):
        pass

    def test_pk_set_none(self):
        pass

    def test_task_none(self):
        pass

    def test_removing_adviser_does_not_trigger_signals(self):
        pass
