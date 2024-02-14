import datetime
from importlib import import_module
from unittest.mock import MagicMock


from django.apps import apps

from datahub.core.test_utils import APITestMixin
from datahub.task.models import Task


from datahub.company.test.factories import AdviserFactory
from datahub.task.test.factories import TaskFactory


class TestTaskMigrations(APITestMixin):
    def test_reminder_due_date_migration_forwards_func(self):
        # Import migration file dynamically as it start with a number
        module = import_module('datahub.task.migrations.0005_task_reminder_date')

        task = TaskFactory(reminder_days=7, due_date=datetime.date.today())
        module.forwards_func(apps, None)

        assert task.reminder_date == task.due_date - datetime.timedelta(days=task.reminder_days)

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

    def test_archive_task_status_migration_forwards_func(self):
        # Import migration file dynamically as it start with a number
        module = import_module('datahub.task.migrations.0011_archive_task_status')

        task_archived = TaskFactory(archived=True, archived_by=AdviserFactory())
        task = TaskFactory(archived=False)

        module.forwards_func(apps, None)

        task_archived = Task.objects.get(pk=task_archived.id)
        task = Task.objects.get(pk=task.id)

        assert task_archived.status == Task.Status.COMPLETE
        assert task_archived.archived is False
        assert task_archived.archived_by is None
        assert task.status == Task.Status.ACTIVE
        assert task.archived is False
        assert task.archived_by is None

    def test_archive_task_status_migration_reverse_func(self):
        # Import migration file dynamically as it start with a number
        module = import_module('datahub.task.migrations.0011_archive_task_status')

        task_archived = TaskFactory(status=Task.Status.COMPLETE)
        task = TaskFactory(status=Task.Status.ACTIVE)

        module.reverse_func(apps, None)

        task_archived = Task.objects.get(pk=task_archived.id)
        task = Task.objects.get(pk=task.id)

        assert task_archived.archived is True
        assert task.archived is False
