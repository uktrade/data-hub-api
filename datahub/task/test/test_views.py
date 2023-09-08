from uuid import uuid4

from django.utils.timezone import now

from faker import Faker

from rest_framework import status
from rest_framework.reverse import reverse


from datahub.company.test.factories import AdviserFactory
from datahub.core.test_utils import (
    APITestMixin,
)

from datahub.task.test.factories import TaskFactory


class TestGetTasks(APITestMixin):
    def test_get_all_tasks_returns_empty_when_no_tasks_exist(self):
        url = reverse('api-v4:task:collection')
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

        url = f'{reverse("api-v4:task:collection")}?archived=false'

        response = self.api_client.get(url).json()
        assert response['count'] == 1
        assert response['results'][0]['id'] == str(not_archived_task.id)

    def test_get_all_tasks_returns_archived_tasks(self):
        archived_task = TaskFactory(archived=True)
        TaskFactory(archived=False)

        url = f'{reverse("api-v4:task:collection")}?archived=true'

        response = self.api_client.get(url).json()
        assert response['count'] == 1
        assert response['results'][0]['id'] == str(archived_task.id)

    def test_get_all_tasks_returns_tasks_belonging_to_an_adviser(self):
        adviser = AdviserFactory()
        adviser_tasks = TaskFactory.create_batch(2, advisers=[adviser])
        TaskFactory.create_batch(3)

        url = f'{reverse("api-v4:task:collection")}?advisers={adviser.id}'

        response = self.api_client.get(url).json()
        assert response['count'] == len(adviser_tasks)
        task_ids = [str(x.id) for x in adviser_tasks]

        for result in response['results']:
            assert result['id'] in task_ids

    def test_get_all_tasks_returns_no_tasks_when_adviser_has_no_assigned_tasks(self):
        adviser = AdviserFactory()
        TaskFactory.create_batch(3)

        url = f'{reverse("api-v4:task:collection")}?advisers={adviser.id}'

        response = self.api_client.get(url).json()
        assert response == {
            'count': 0,
            'next': None,
            'previous': None,
            'results': [],
        }


class TestGetTask(APITestMixin):
    def test_get_task_return_404_when_task_id_unknown(self):
        TaskFactory()

        url = reverse(
            'api-v4:task:item',
            kwargs={'pk': uuid4()},
        )
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_task_return_task_when_task_id_valid(self):
        task = TaskFactory()

        url = reverse(
            'api-v4:task:item',
            kwargs={'pk': task.id},
        )
        response = self.api_client.get(url).json()
        expected_response = {
            'id': str(task.id),
            'title': task.title,
            'description': task.description,
            'due_date': task.due_date,
            'reminder_days': task.reminder_days,
            'email_reminders_enabled': task.email_reminders_enabled,
            'advisers': [
                {
                    'id': str(adviser.id),
                    'name': adviser.name,
                    'first_name': adviser.first_name,
                    'last_name': adviser.last_name,
                }
                for adviser in task.advisers.all()
            ],
            'archived': task.archived,
            'archived_by': task.archived_by,
            'created_by': {
                'name': task.created_by.name,
                'first_name': task.created_by.first_name,
                'last_name': task.created_by.last_name,
                'id': str(task.created_by.id),
            },
            'modified_by': {
                'name': task.modified_by.name,
                'first_name': task.modified_by.first_name,
                'last_name': task.modified_by.last_name,
                'id': str(task.modified_by.id),
            },
        }
        assert response == expected_response


class TestCreateTask(APITestMixin):
    def test_create_task_with_missing_mandatory_fields_returns_bad_request(self):
        url = reverse('api-v4:task:collection')

        response = self.api_client.post(
            url,
            data={},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert list(response.json().keys()) == ['title', 'advisers']

    def test_create_task_with_unknown_advisor_id_returns_bad_request(self):
        faker = Faker()

        url = reverse('api-v4:task:collection')

        response = self.api_client.post(
            url,
            data={'title': faker.word(), 'advisers': [uuid4()]},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert list(response.json().keys()) == ['advisers']

    def test_create_task_with_valid_mandatory_fields_returns_success_created(self):
        faker = Faker()

        adviser = AdviserFactory()

        url = reverse('api-v4:task:collection')

        new_task = {
            'title': faker.word(),
            'description': faker.word(),
            'due_date': now().date(),
            'reminder_days': 3,
            'email_reminders_enabled': True,
            'advisers': [adviser.id],
        }

        post_response = self.api_client.post(
            url,
            data=new_task,
        )
        post_response_json = post_response.json()

        assert post_response.status_code == status.HTTP_201_CREATED

        get_url = reverse(
            'api-v4:task:item',
            kwargs={'pk': post_response_json['id']},
        )
        get_response = self.api_client.get(get_url)

        assert get_response.status_code == status.HTTP_200_OK
        expected_response = {
            'id': post_response_json['id'],
            'title': post_response_json['title'],
            'description': post_response_json['description'],
            'due_date': post_response_json['due_date'],
            'reminder_days': post_response_json['reminder_days'],
            'email_reminders_enabled': post_response_json['email_reminders_enabled'],
            'advisers': [
                {
                    'id': str(adviser.id),
                    'name': adviser.name,
                    'first_name': adviser.first_name,
                    'last_name': adviser.last_name,
                },
            ],
            'archived': post_response_json['archived'],
            'archived_by': post_response_json['archived_by'],
            'created_by': {
                'name': self.user.name,
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'id': str(self.user.id),
            },
            'modified_by': {
                'name': self.user.name,
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'id': str(self.user.id),
            },
        }
        assert get_response.json() == expected_response


class TestEditTask(APITestMixin):
    def test_edit_task_return_404_when_task_id_unknown(self):
        url = reverse('api-v4:task:item', kwargs={'pk': uuid4()})

        response = self.api_client.patch(
            url,
            data={'title': 'abc'},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_edit_task_with_unknown_advisor_id_returns_bad_request(self):
        task = TaskFactory()

        url = reverse('api-v4:task:item', kwargs={'pk': task.id})

        response = self.api_client.patch(
            url,
            data={'advisers': [uuid4()]},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert list(response.json().keys()) == ['advisers']

    def test_edit_task_with_valid_fields_returns_success(self):
        task = TaskFactory()
        new_adviser = AdviserFactory()

        url = reverse('api-v4:task:item', kwargs={'pk': task.id})

        response = self.api_client.patch(
            url,
            data={'advisers': [new_adviser.id]},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['advisers'][0]['id'] == str(new_adviser.id)


class TestArchiveTask(APITestMixin):
    def test_archive_task_without_reason_returns_bad_request(self):
        task = TaskFactory()
        url = reverse('api-v4:task:archive', kwargs={'pk': task.id})
        response = self.api_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {
            'reason': ['This field is required.'],
        }

    def test_archive_task_with_valid_reason_returns_success(self):
        task = TaskFactory()
        url = reverse('api-v4:task:archive', kwargs={'pk': task.id})
        response = self.api_client.post(url, data={'reason': 'completed'})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['archived']
        assert response.data['archived_by'] == {
            'id': str(self.user.pk),
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'name': self.user.name,
        }
        assert response.data['archived_reason'] == 'completed'
        assert response.data['id'] == str(task.id)
