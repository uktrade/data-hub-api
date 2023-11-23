import datetime
from importlib import import_module
from unittest.mock import MagicMock


from django.apps import apps

from datahub.core.test_utils import APITestMixin
from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.task.models import Task


from datahub.task.test.factories import TaskFactory


class TestTaskMigrations(APITestMixin):
    def test_reminder_due_date_migration_forwards_func(self):
        # Import migration file dynamically as it start with a number
        module = import_module('datahub.task.migrations.0005_task_reminder_date')

        task = TaskFactory(reminder_days=7, due_date=datetime.date.today())
        module.forwards_func(apps, None)

        assert task.reminder_date == task.due_date - datetime.timedelta(days=task.reminder_days)

    def test_add_investment_project_to_task_migration_forwards_func(self):
        # Import migration file dynamically as it start with a number
        module = import_module('datahub.task.migrations.0006_task_investment_project')

        investment_project = InvestmentProjectFactory()
        task = TaskFactory(reminder_days=7, due_date=datetime.date.today())

        investment_project_task_class = apps.get_model('task', 'InvestmentProjectTask')

        investment_project_task = investment_project_task_class(
            task=task,
            investment_project=investment_project,
        )

        investment_project_task.save()

        module.forwards_func(apps, None)

        updated_task = Task.objects.filter(id=task.id).first()

        assert updated_task.investment_project.id == investment_project.id

    def test_task_migration_forwards_func_ignored_when_investment_project_model_missing(
        self,
    ):
        # Import migration file dynamically as it start with a number
        module = import_module('datahub.task.migrations.0006_task_investment_project')

        task = TaskFactory(reminder_days=7, due_date=datetime.date.today())

        apps = MagicMock()
        apps.get_model.return_value = None

        module.forwards_func(apps, None)

        updated_task = Task.objects.filter(id=task.id).first()

        assert updated_task.investment_project is None
