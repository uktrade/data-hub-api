from datetime import datetime, timezone

import pytest
from django.urls import reverse
from freezegun import freeze_time
from rest_framework import status

from datahub.company.test.factories import CompanyFactory
from datahub.core.test_utils import format_date_or_datetime
from datahub.dataset.core.test import BaseDatasetViewTest
from datahub.interaction.test.factories import InteractionFactoryBase
from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.task.models import Task
from datahub.task.test.factories import TaskFactory


def get_expected_data_from_task(task):
    """Returns task data as a dictionary"""
    data = {
        'created_on': format_date_or_datetime(task.created_on),
        'created_by_id': str(task.created_by_id),
        'modified_on': format_date_or_datetime(task.modified_on),
        'modified_by_id': str(task.modified_by_id) if task.modified_by else None,
        'archived': task.archived,
        'archived_on': format_date_or_datetime(task.archived_on),
        'archived_by_id': str(task.archived_by_id) if task.archived_by else None,
        'archived_reason': task.archived_reason,
        'id': str(task.id),
        'title': task.title,
        'description': task.description,
        'due_date': format_date_or_datetime(task.due_date),
        'reminder_days': task.reminder_days,
        'email_reminders_enabled': task.email_reminders_enabled,
        'adviser_ids': [str(adviser.id) for adviser in task.advisers.all().order_by('first_name')],
        'reminder_date': task.reminder_date,
        'investment_project_id': str(task.investment_project.id)
        if task.investment_project else None,
        'company_id': str(task.company.id) if task.company else None,
        'interaction_id': str(task.interaction.id) if task.interaction else None,
        'status': task.status.value,
    }
    return data


@pytest.mark.django_db
class TestTasksDatasetViewSet(BaseDatasetViewTest):
    """
    Tests for TasksDatasetView
    """

    view_url = reverse('api-v4:dataset:tasks-dataset')
    factory = TaskFactory

    def test_success_with_one(self, data_flow_api_client):
        """Test that the endpoint returns expected data for a single task."""
        task = self.factory(
            investment_project=InvestmentProjectFactory(),
        )
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK

        results_from_response = response.json()['results']
        assert len(results_from_response) == 1

        task_from_response = results_from_response[0]
        expected_task = get_expected_data_from_task(task)
        assert task_from_response == expected_task

    def test_success_with_multiple(self, data_flow_api_client):
        """Test that the endpoint returns expected data for multiple tasks."""
        task_one = self.factory(
            investment_project=InvestmentProjectFactory(),
        )
        task_two = self.factory(
            company=CompanyFactory(),
        )

        task_three = self.factory(
            interaction=InteractionFactoryBase(),
        )
        task_four = self.factory(
            investment_project=InvestmentProjectFactory(),
        )

        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK

        results_from_response = response.json()['results']
        assert len(results_from_response) == 4

        tasks_from_response = results_from_response
        expected_tasks = [
            get_expected_data_from_task(task)
            for task
            in [task_one, task_two, task_three, task_four]
        ]
        assert tasks_from_response == expected_tasks

    def test_with_updated_since_filter(self, data_flow_api_client):
        """Test that the endpoint returns only tasks modified after a certain date."""
        with freeze_time('2024-01-01 12:00:00'):
            # task_one
            self.factory(
                investment_project=InvestmentProjectFactory(),
            )
            task_two = self.factory(
                investment_project=InvestmentProjectFactory(),
            )
        with freeze_time('2024-01-02 12:00:00'):
            task_three = self.factory(
                company=CompanyFactory(),
            )
        with freeze_time('2024-01-03 12:00:00'):
            task_two.status = Task.Status.COMPLETE
            task_two.save()  # save task_two to trigger an update to `modified_on` field
            task_four = self.factory(
                interaction=InteractionFactoryBase(),
            )

        updated_since_date = datetime(2024, 1, 2, tzinfo=timezone.utc).strftime('%Y-%m-%d')
        response = data_flow_api_client.get(self.view_url, {'updated_since': updated_since_date})
        assert response.status_code == status.HTTP_200_OK

        results_from_response = response.json()['results']
        assert len(results_from_response) == 3

        tasks_from_response = results_from_response
        expected_tasks = [
            get_expected_data_from_task(task)
            for task
            in [task_two, task_three, task_four]
        ]
        assert tasks_from_response == expected_tasks
