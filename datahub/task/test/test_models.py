import datetime

import pytest

from datahub.task.models import Task
from datahub.task.test.factories import AdviserFactory, InvestmentProjectTaskFactory, TaskFactory

pytestmark = pytest.mark.django_db


class TestTaskModel:
    """Tests for the Task model."""

    def test_task_with_no_due_date_or_reminder_days_has_no_reminder_date(self):
        obj = Task()
        obj.save()
        assert not obj.reminder_date

    def test_task_with_due_date_but_no_reminder_days_has_no_reminder_date(self):
        obj = Task(due_date=datetime.date(2030, 10, 10))
        obj.save()
        assert not obj.reminder_date

    def test_task_with_no_due_date_but_a_reminder_days_has_no_reminder_date(self):
        obj = Task(reminder_days=1)
        obj.save()
        assert not obj.reminder_date

    def test_task_with_due_date_and_reminder_days_has_a_reminder_date(self):
        obj = Task(reminder_days=3, due_date=datetime.date(2030, 10, 10))
        obj.save()
        assert obj.reminder_date == datetime.date(2030, 10, 7)

    def test_task_reminder_date_updates_on_changes_to_reminder_days(
        self,
    ):
        obj = Task(reminder_days=3, due_date=datetime.date(2030, 10, 10))
        obj.save()
        assert obj.reminder_date == datetime.date(2030, 10, 7)
        obj.reminder_days = 8
        obj.save()
        assert obj.reminder_date == datetime.date(2030, 10, 2)

    def test_task_get_company_for_investment_project(self):
        investment_project_task = InvestmentProjectTaskFactory()
        assert (
            investment_project_task.task.get_company()
            == investment_project_task.investment_project.investor_company
        )
