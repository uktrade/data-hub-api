import datetime

from unittest.mock import patch
from uuid import uuid4


import pytest

from django.utils.timezone import now

from faker import Faker

from rest_framework import status
from rest_framework.reverse import reverse


from datahub.company.test.factories import AdviserFactory
from datahub.core.test_utils import (
    APITestMixin,
    format_date_or_datetime,
)
from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.task.models import InvestmentProjectTask, Task

from datahub.task.test.factories import InvestmentProjectTaskFactory, TaskFactory
from datahub.task.test.utils import BaseListTaskTests
from datahub.task.views import InvestmentProjectTaskV4ViewSet


class TestListInvestmentProjectTask(BaseListTaskTests):
    """Test the LIST investment project task endpoint"""

    reverse_url = 'api-v4:task:investment_project_task_collection'
    task_type_factory = InvestmentProjectTaskFactory

    def test_get_all_tasks_returns_error_when_query_params_are_invalid(self):
        InvestmentProjectFactory()

        url = f'{reverse(self.reverse_url)}?investment_project=not_valid'

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert list(response.json().keys()) == ['investment_project']

    def test_get_all_tasks_returns_only_investment_project_tasks_when_filtering(self):
        investment_project = InvestmentProjectFactory()
        investment_project_tasks = InvestmentProjectTaskFactory.create_batch(
            2,
            investment_project=investment_project,
        )
        InvestmentProjectTaskFactory()

        url = f'{reverse(self.reverse_url)}?investment_project={investment_project.id}'

        task_ids = [str(x.id) for x in investment_project_tasks]

        response = self.api_client.get(url).json()

        assert response['count'] == 2
        for result in response['results']:
            assert result['id'] in task_ids

    def test_get_all_tasks_returns_ordered_investment_project_tasks_when_sortby_param_is_used(
        self,
    ):
        earliest_task = InvestmentProjectTaskFactory(
            task=TaskFactory(due_date=datetime.date.today() - datetime.timedelta(days=1)),
        )
        latest_task = InvestmentProjectTaskFactory(
            task=TaskFactory(due_date=datetime.date.today() + datetime.timedelta(days=1)),
        )
        middle_task = InvestmentProjectTaskFactory(
            task=TaskFactory(due_date=datetime.date.today()),
        )

        url = f'{reverse(self.reverse_url)}?sortby=task__due_date'

        response = self.api_client.get(url).json()

        ordered_ids_response = [result['id'] for result in response['results']]
        assert ordered_ids_response == [
            str(earliest_task.id),
            str(middle_task.id),
            str(latest_task.id),
        ]


class TestGetInvestmentProjectTask(APITestMixin):
    """Test the GET investment project task endpoint"""

    def test_get_task_return_404_when_task_id_unknown(self):
        InvestmentProjectTaskFactory()

        url = reverse(
            'api-v4:task:investment_project_task_item',
            kwargs={'pk': uuid4()},
        )
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_task_return_task_when_task_id_valid(self):
        investment_task = InvestmentProjectTaskFactory()
        url = reverse(
            'api-v4:task:investment_project_task_item',
            kwargs={'pk': investment_task.id},
        )
        response = self.api_client.get(url).json()
        expected_response = {
            'id': str(investment_task.id),
            'investment_project': {
                'name': investment_task.investment_project.name,
                'id': str(investment_task.investment_project.id),
            },
            'task': {
                'id': str(investment_task.task.id),
                'title': investment_task.task.title,
                'description': investment_task.task.description,
                'due_date': investment_task.task.due_date,
                'reminder_days': investment_task.task.reminder_days,
                'email_reminders_enabled': investment_task.task.email_reminders_enabled,
                'advisers': [
                    {
                        'id': str(adviser.id),
                        'name': adviser.name,
                        'first_name': adviser.first_name,
                        'last_name': adviser.last_name,
                    }
                    for adviser in investment_task.task.advisers.all()
                ],
                'archived': investment_task.task.archived,
                'archived_by': investment_task.task.archived_by,
                'archived_reason': investment_task.task.archived_reason,
                'created_by': {
                    'name': investment_task.task.created_by.name,
                    'first_name': investment_task.task.created_by.first_name,
                    'last_name': investment_task.task.created_by.last_name,
                    'id': str(investment_task.task.created_by.id),
                },
                'modified_by': {
                    'name': investment_task.task.modified_by.name,
                    'first_name': investment_task.task.modified_by.first_name,
                    'last_name': investment_task.task.modified_by.last_name,
                    'id': str(investment_task.task.modified_by.id),
                },
                'created_on': format_date_or_datetime(investment_task.task.created_on),
                'modified_on': format_date_or_datetime(investment_task.task.modified_on),
            },
            'created_by': {
                'name': investment_task.created_by.name,
                'first_name': investment_task.created_by.first_name,
                'last_name': investment_task.created_by.last_name,
                'id': str(investment_task.created_by.id),
            },
            'modified_by': {
                'name': investment_task.modified_by.name,
                'first_name': investment_task.modified_by.first_name,
                'last_name': investment_task.modified_by.last_name,
                'id': str(investment_task.modified_by.id),
            },
            'created_on': format_date_or_datetime(investment_task.created_on),
            'modified_on': format_date_or_datetime(investment_task.modified_on),
        }
        assert response == expected_response


class TestAddInvestmentProjectTask(APITestMixin):
    """Test the POST investment project task endpoint"""

    def test_create_task_with_missing_mandatory_fields_returns_bad_request(self):
        url = reverse('api-v4:task:investment_project_task_collection')

        response = self.api_client.post(
            url,
            data={},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert list(response.json().keys()) == ['investment_project', 'task']

    def test_create_task_with_unknown_advisor_id_returns_bad_request(self):
        faker = Faker()

        url = reverse('api-v4:task:investment_project_task_collection')
        investment_project = InvestmentProjectFactory()

        response = self.api_client.post(
            url,
            data={
                'investment_project': investment_project.id,
                'task': {'title': faker.word(), 'advisers': [uuid4()]},
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert list(response.json()['task'].keys()) == ['advisers']

    def test_create_task_with_unknown_investment_project_id_returns_bad_request(self):
        faker = Faker()

        url = reverse('api-v4:task:investment_project_task_collection')
        adviser = AdviserFactory()

        response = self.api_client.post(
            url,
            data={
                'investment_project': uuid4(),
                'task': {'title': faker.word(), 'advisers': [adviser.id]},
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert list(response.json().keys()) == ['investment_project']

    def test_create_task_with_valid_mandatory_fields_returns_success_created(self):
        faker = Faker()

        adviser = AdviserFactory()
        investment_project = InvestmentProjectFactory()

        url = reverse('api-v4:task:investment_project_task_collection')

        new_investment_task = {
            'investment_project': investment_project.id,
            'task': {
                'title': faker.word(),
                'description': faker.word(),
                'due_date': now().date(),
                'reminder_days': 3,
                'email_reminders_enabled': True,
                'advisers': [adviser.id],
            },
        }

        post_response = self.api_client.post(
            url,
            data=new_investment_task,
        )
        post_response_json = post_response.json()

        assert post_response.status_code == status.HTTP_201_CREATED

        get_url = reverse(
            'api-v4:task:investment_project_task_item',
            kwargs={'pk': post_response_json['id']},
        )
        get_response = self.api_client.get(get_url)

        assert get_response.status_code == status.HTTP_200_OK
        assert get_response.json()['id'] == post_response_json['id']

    @patch.object(InvestmentProjectTaskV4ViewSet, 'create_and_save_task_type_model')
    def test_create_task_success_but_add_investment_task_fails_an_orphan_task_not_created(
        self,
        save_task,
    ):
        """
        Test when the task is added but the investment project task fails to add, there is
        not an orphaned task in the system
        """
        save_task.side_effect = NotImplementedError()

        faker = Faker()

        adviser = AdviserFactory()
        investment_project = InvestmentProjectFactory()

        url = reverse('api-v4:task:investment_project_task_collection')

        new_investment_task = {
            'investment_project': investment_project.id,
            'task': {
                'title': faker.word(),
                'description': faker.word(),
                'due_date': now().date(),
                'reminder_days': 3,
                'email_reminders_enabled': True,
                'advisers': [adviser.id],
            },
        }

        with pytest.raises(NotImplementedError):
            self.api_client.post(
                url,
                data=new_investment_task,
            )

        assert Task.objects.exists() is False
        assert InvestmentProjectTask.objects.exists() is False
