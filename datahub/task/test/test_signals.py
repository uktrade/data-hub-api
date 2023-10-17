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
