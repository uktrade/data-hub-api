from unittest import mock
from unittest.mock import patch
import pytest

from datahub.company.test.factories import AdviserFactory
from datahub.reminder.models import (
    TaskAssignedToMeFromOthersSubscription,
    TaskOverdueSubscription,
    UpcomingTaskReminderSubscription,
)
from datahub.task.models import Task
from datahub.task.test.factories import InvestmentProjectTaskFactory, TaskFactory


@pytest.mark.django_db
class TestDeleteInvestmentProjectTask:
    def test_delete_investment_project_task__without_linked_tasks_does_nothing(self):
        task = TaskFactory()
        task_id = task.id

        investment_project_task = InvestmentProjectTaskFactory(task=task)
        task.delete()
        investment_project_task.delete()

        obj = Task.objects.filter(pk=task_id).first()
        assert obj is None

    def test_delete_investment_project_task_deletes_linked_task(self):
        task = TaskFactory()
        task_id = task.id

        investment_project_task = InvestmentProjectTaskFactory(task=task)
        investment_project_task.delete()

        obj = Task.objects.filter(pk=task_id).first()
        assert obj is None


class SubscriptionBaseTestMixin():
    def test_creation_of_single_adviser_subscription_on_task_creation(self):
        TaskFactory()
        adviser = AdviserFactory()
        TaskFactory(advisers=[adviser])
        subscriptions = self.subscription.objects.filter(adviser=adviser)

        assert subscriptions.count() == 1

        TaskFactory()
        TaskFactory()
        TaskFactory(advisers=[adviser])
        subscriptions = self.subscription.objects.filter(adviser=adviser)

        assert subscriptions.count() == 1

    def test_creation_of_multiple_adviser_subscription_on_task_creation(self):
        TaskFactory()
        adviser1 = AdviserFactory()
        adviser2 = AdviserFactory()
        AdviserFactory()
        TaskFactory(advisers=[adviser1, adviser2])
        subscriptions = self.subscription.objects.filter(
            adviser__in=[adviser1, adviser2],
        )

        assert subscriptions.count() == 2

        """
        Test that only additional subscriptions for new advisers is created
        """
        adviser3 = AdviserFactory()
        TaskFactory(advisers=[adviser1, adviser2, adviser3])
        subscriptions = self.subscription.objects.filter(
            adviser__in=[adviser1, adviser2, adviser3],
        )

        assert subscriptions.count() == 3


@pytest.mark.django_db
class TestTaskReminderSubscription(SubscriptionBaseTestMixin):
    subscription = UpcomingTaskReminderSubscription


@pytest.mark.django_db
class TestTaskOverdueSubscription(SubscriptionBaseTestMixin):
    subscription = TaskOverdueSubscription


@pytest.mark.django_db
class TestTaskAssignedToMeFromOthersSubscription(SubscriptionBaseTestMixin):
    subscription = TaskAssignedToMeFromOthersSubscription


@pytest.mark.django_db
class TestTaskAdviserChangedSubscriptions:
    @patch('datahub.task.signals.schedule_create_task_reminder_subscription_task')
    @patch('datahub.task.signals.schedule_create_task_assigned_to_me_from_others_subscription_task')
    def test_schedule_functions_called_for_each_adviser(self, mock_create_task_reminder, mock_create_task_assigned_to_me):
        adviser1 = AdviserFactory()
        adviser2 = AdviserFactory()
        task = TaskFactory(advisers=[adviser1, adviser2])

        assert mock_create_task_reminder.call_count == 2

        mock_create_task_reminder.assert_has_calls([
            mock.call(
                adviser1.id,
            ),
            mock.call(
                adviser2.id,
            ),
        ], any_order=True)
        mock_create_task_assigned_to_me.assert_has_calls([
            mock.call(
                adviser_id=adviser1.id,
                task=task,
            ),
            mock.call(
                adviser_id=adviser2.id,
                task=task,
            ),
        ], any_order=True)
