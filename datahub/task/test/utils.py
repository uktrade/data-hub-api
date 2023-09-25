from uuid import uuid4

import factory


from rest_framework import status
from rest_framework.reverse import reverse


from datahub.company.test.factories import AdviserFactory
from datahub.core.test_utils import (
    APITestMixin,
)

from datahub.task.test.factories import TaskFactory


class BaseTaskTests(APITestMixin):
    def adviser_api_client(self, adviser):
        """Create an api client where the adviser is the authenticated user"""
        return self.create_api_client(user=adviser)


class BaseListTaskTests(BaseTaskTests):
    reverse_url = None
    task_type_factory = None

    def test_get_all_tasks_returns_empty_when_no_tasks_exist(self):
        url = reverse(self.reverse_url)
        response = self.api_client.get(url).json()
        assert response == {
            'count': 0,
            'next': None,
            'previous': None,
            'results': [],
        }

    def test_get_all_tasks_returns_not_archived_tasks(self):
        TaskFactory(archived=True)
        not_archived_task = TaskFactory(archived=False)
        id = not_archived_task.id

        if self.task_type_factory:
            task_type = self.task_type_factory(task=not_archived_task)
            id = task_type.id

        url = f'{reverse(self.reverse_url)}?archived=false'

        response = self.api_client.get(url).json()
        assert response['count'] == 1
        assert response['results'][0]['id'] == str(id)

    def test_get_all_tasks_returns_archived_tasks(self):
        archived_task = TaskFactory(archived=True)
        TaskFactory(archived=False)
        id = archived_task.id

        if self.task_type_factory:
            task_type = self.task_type_factory(task=archived_task)
            id = task_type.id

        url = f'{reverse(self.reverse_url)}?archived=true'

        response = self.api_client.get(url).json()
        assert response['count'] == 1
        assert response['results'][0]['id'] == str(id)

    def test_get_all_tasks_returns_tasks_belonging_to_an_adviser(self):
        adviser = AdviserFactory()
        adviser_tasks = TaskFactory.create_batch(2, advisers=[adviser])
        TaskFactory.create_batch(3)
        task_ids = [str(x.id) for x in adviser_tasks]

        if self.task_type_factory:
            task_types = self.task_type_factory.create_batch(
                2,
                task=factory.Iterator(adviser_tasks),
            )
            task_ids = [str(x.id) for x in task_types]

        url = f'{reverse(self.reverse_url)}?advisers={adviser.id}'

        response = self.api_client.get(url).json()
        assert response['count'] == len(adviser_tasks)

        for result in response['results']:
            assert result['id'] in task_ids

    def test_get_all_tasks_returns_no_tasks_when_adviser_has_no_assigned_tasks(self):
        adviser = AdviserFactory()
        TaskFactory.create_batch(3)

        url = f'{reverse(self.reverse_url)}?advisers={adviser.id}'

        response = self.api_client.get(url).json()
        assert response == {
            'count': 0,
            'next': None,
            'previous': None,
            'results': [],
        }


class BaseEditTaskTests(BaseTaskTests):
    reverse_url = None
    task_type_factory = None
    nested_task_field_name = None

    def test_edit_task_with_unknown_advisor_id_returns_bad_request(self):
        adviser = AdviserFactory()
        task = TaskFactory(created_by=adviser)

        data = {'advisers': [uuid4()]}

        response = self._call_task_endpoint_assert_response(
            adviser,
            task,
            data,
            status.HTTP_400_BAD_REQUEST,
        )

        json = response.json()

        if self.nested_task_field_name:
            json = json.get(self.nested_task_field_name)

        assert list(json.keys()) == ['advisers']

    def test_edit_task_returns_forbidden_when_user_not_creator_or_assigned_to_task(self):
        task = TaskFactory()
        adviser = AdviserFactory()

        data = {'advisers': [adviser.id]}
        self._call_task_endpoint_assert_response(adviser, task, data, status.HTTP_403_FORBIDDEN)

    def test_edit_task_returns_success_when_user_is_creator_but_not_assigned_to_task(self):
        adviser = AdviserFactory()
        task = TaskFactory(created_by=adviser)

        data = {'advisers': [adviser.id]}

        self._call_task_endpoint_assert_response(adviser, task, data, status.HTTP_200_OK)

    def test_edit_task_returns_success_when_user_is_not_creator_but_is_assigned_to_task(self):
        adviser = AdviserFactory()
        task = TaskFactory(advisers=[adviser])

        data = {'advisers': [adviser.id]}

        self._call_task_endpoint_assert_response(adviser, task, data, status.HTTP_200_OK)

    def test_edit_task_returns_success_when_user_is_creator_and_is_assigned_to_task(self):
        adviser = AdviserFactory()
        task = TaskFactory(advisers=[adviser], created_by=adviser)

        data = {'advisers': [adviser.id]}

        self._call_task_endpoint_assert_response(adviser, task, data, status.HTTP_200_OK)

    def _call_task_endpoint_assert_response(self, adviser, task, data, status_code):
        """
        Call the task endpoint and check the response is expected
        """
        id = task.id

        if self.task_type_factory:
            task_type = self.task_type_factory(task=task, created_by=task.created_by)
            id = task_type.id
            data = {'task': data}

        url = reverse(self.reverse_url, kwargs={'pk': id})

        response = self.adviser_api_client(adviser).patch(
            url,
            data,
        )

        assert response.status_code == status_code
        return response
