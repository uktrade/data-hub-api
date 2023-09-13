import pytest

from datahub.task.models import Task
from datahub.task.test.factories import InvestmentProjectTaskFactory, TaskFactory


@pytest.mark.django_db
class TestDeleteInvestmentProjectTask:
    def test_delete_investment_project_task_deletes_linked_task(self):
        task = TaskFactory()
        task_id = task.id

        investment_project_task = InvestmentProjectTaskFactory(task=task)
        investment_project_task.delete()

        obj = Task.objects.filter(pk=task_id).first()
        assert obj is None
