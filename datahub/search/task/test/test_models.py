import pytest

from datahub.investment.project.test.factories import InvestmentProjectFactory

from datahub.search.task.apps import TaskSearchApp
from datahub.search.task.models import Task
from datahub.task.test.factories import TaskFactory

pytestmark = pytest.mark.django_db


def test_task_to_dict(opensearch):
    """Test for generic task search model"""
    task = TaskFactory()
    result = Task.db_object_to_dict(task)

    assert result == {
        '_document_type': TaskSearchApp.name,
        'id': task.id,
        'created_by': {
            'id': str(task.created_by.id),
            'first_name': task.created_by.first_name,
            'name': task.created_by.name,
            'last_name': task.created_by.last_name,
        },
        'title': task.title,
        'description': task.description,
        'due_date': task.due_date,
        'reminder_days': task.reminder_days,
        'email_reminders_enabled': task.email_reminders_enabled,
        'reminder_date': task.reminder_date,
        'investment_project': None,
        'modified_on': task.modified_on,
        'archived': False,
        'company': None,
        'advisers': [
            {
                'id': str(adviser.id),
                'name': adviser.name,
                'first_name': adviser.first_name,
                'last_name': adviser.last_name,
            }
            for adviser in task.advisers.all()
        ],
    }


def test_investment_project_task_to_dict(opensearch):
    """Test for investment project task fields to search model"""
    investment_project = InvestmentProjectFactory()

    task = TaskFactory(
        investment_project=investment_project,
    )
    company = task.get_company()

    result = Task.db_object_to_dict(task)

    assert result['investment_project'] == {
        'id': str(investment_project.id),
        'name': investment_project.name,
        'project_code': investment_project.project_code,
    }
    assert result['company'] == {'id': str(company.id), 'name': company.name}
