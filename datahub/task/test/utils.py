import factory


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
