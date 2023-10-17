import pytest

from datahub.company.test.factories import AdviserFactory
from datahub.reminder.models import (
    TaskAssignedToMeFromOthersSubscription,
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


@pytest.mark.django_db
class TestTaskReminderSubscription:
    def test_creation_of_single_adviser_subscription_on_task_creation(self):
        TaskFactory()
        adviser = AdviserFactory()
        TaskFactory(advisers=[adviser])
        subscriptions = UpcomingTaskReminderSubscription.objects.filter(adviser=adviser)

        assert subscriptions.count() == 1

        TaskFactory()
        TaskFactory()
        TaskFactory(advisers=[adviser])
        subscriptions = UpcomingTaskReminderSubscription.objects.filter(adviser=adviser)

        assert subscriptions.count() == 1

    def test_creation_of_multiple_adviser_subscription_on_task_creation(self):
        TaskFactory()
        adviser1 = AdviserFactory()
        adviser2 = AdviserFactory()
        AdviserFactory()
        TaskFactory(advisers=[adviser1, adviser2])
        subscriptions = UpcomingTaskReminderSubscription.objects.filter(
            adviser__in=[adviser1, adviser2],
        )

        assert subscriptions.count() == 2

        """
        Test that only additional subscriptions for new advisers is created
        """
        adviser3 = AdviserFactory()
        TaskFactory(advisers=[adviser1, adviser2, adviser3])
        subscriptions = UpcomingTaskReminderSubscription.objects.filter(
            adviser__in=[adviser1, adviser2, adviser3],
        )

        assert subscriptions.count() == 3


@pytest.mark.django_db
class TestTaskAssignedToMeFromOthersSubscription:
    def test_creation_of_single_adviser_subscription_on_task_creation(self):
        TaskFactory()
        adviser = AdviserFactory()
        TaskFactory(advisers=[adviser])
        subscriptions = TaskAssignedToMeFromOthersSubscription.objects.filter(adviser=adviser)

        assert subscriptions.count() == 1

        TaskFactory()
        TaskFactory()
        TaskFactory(advisers=[adviser])
        subscriptions = TaskAssignedToMeFromOthersSubscription.objects.filter(adviser=adviser)

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

        """
        Test that only additional subscriptions for new advisers is created
        """
        adviser3 = AdviserFactory()
        TaskFactory(advisers=[adviser1, adviser2, adviser3])
        subscriptions = TaskAssignedToMeFromOthersSubscription.objects.filter(
            adviser__in=[adviser1, adviser2, adviser3],
        )

        assert subscriptions.count() == 3
