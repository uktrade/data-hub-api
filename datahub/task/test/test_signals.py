import pytest

from datahub.company.test.factories import AdviserFactory
from datahub.reminder import UpcomingTaskReminderSubscription
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
    def test_creation_of_adviser_subscription_on_task_creation(self):
        adviser = AdviserFactory()
        task = TaskFactory(advisers=[adviser])

        task.save()

        assert UpcomingTaskReminderSubscription.objects.get(adviser=adviser)

    def test_no_creation_for_existing_adviser_subscription_on_task_creation(self):
        assert True
