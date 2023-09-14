from uuid import uuid4

import factory

from django.utils.timezone import now

from faker import Faker

from rest_framework import status
from rest_framework.reverse import reverse


from datahub.company.test.factories import AdviserFactory
from datahub.investment.project.test.factories import (
    InvestmentProjectFactory,
)

from datahub.core.test_utils import (
    APITestMixin,
    format_date_or_datetime,
)

from datahub.task.test.factories import InvestmentProjectTaskFactory, TaskFactory


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


class TestTaskV4ViewSet:
    class TestListTask(BaseListTaskTests):
        """Test the LIST task endpoint"""

        reverse_url = 'api-v4:task:collection'

    class TestGetTask(APITestMixin):
        """Test the GET task endpoint"""

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
                'archived_reason': task.archived_reason,
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
                'created_on': format_date_or_datetime(task.created_on),
            }
            assert response == expected_response

    class TestAddTask(APITestMixin):
        """Test the POST task endpoint"""

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
                'archived_reason': post_response_json['archived_reason'],
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
                'created_on': post_response_json['created_on'],
            }
            assert get_response.json() == expected_response

    class TestEditTask(BaseTaskTests):
        """Test the PATCH task endpoint"""

        def test_edit_task_return_404_when_task_id_unknown(self):
            url = reverse('api-v4:task:item', kwargs={'pk': uuid4()})

            response = self.api_client.patch(
                url,
                data={'title': 'abc'},
            )
            assert response.status_code == status.HTTP_404_NOT_FOUND

        def test_edit_task_with_unknown_advisor_id_returns_bad_request(self):
            adviser = AdviserFactory()
            task = TaskFactory(created_by=adviser)

            url = reverse('api-v4:task:item', kwargs={'pk': task.id})

            response = self.adviser_api_client(adviser).patch(
                url,
                data={'advisers': [uuid4()]},
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert list(response.json().keys()) == ['advisers']

        def test_edit_task_returns_forbidden_when_user_not_creator_or_assigned_to_task(self):
            task = TaskFactory()
            adviser = AdviserFactory()

            url = reverse('api-v4:task:item', kwargs={'pk': task.id})

            response = self.api_client.patch(
                url,
                data={'advisers': [adviser.id]},
            )

            assert response.status_code == status.HTTP_403_FORBIDDEN

        def test_edit_task_returns_success_when_user_is_creator_but_not_assigned_to_task(self):
            adviser = AdviserFactory()
            task = TaskFactory(created_by=adviser)

            url = reverse('api-v4:task:item', kwargs={'pk': task.id})

            response = self.adviser_api_client(adviser).patch(
                url,
                data={'advisers': [adviser.id]},
            )

            assert response.status_code == status.HTTP_200_OK

        def test_edit_task_returns_success_when_user_is_not_creator_but_is_assigned_to_task(self):
            adviser = AdviserFactory()
            task = TaskFactory(advisers=[adviser])

            url = reverse('api-v4:task:item', kwargs={'pk': task.id})

            response = self.adviser_api_client(adviser).patch(
                url,
                data={'advisers': [adviser.id]},
            )

            assert response.status_code == status.HTTP_200_OK

        def test_edit_task_returns_success_when_user_is_creator_and_is_assigned_to_task(self):
            adviser = AdviserFactory()
            task = TaskFactory(advisers=[adviser], created_by=adviser)

            url = reverse('api-v4:task:item', kwargs={'pk': task.id})

            response = self.adviser_api_client(adviser).patch(
                url,
                data={'advisers': [adviser.id]},
            )

            assert response.status_code == status.HTTP_200_OK

        def test_edit_task_with_valid_fields_returns_success(self):
            adviser = AdviserFactory()
            task = TaskFactory(created_by=adviser)
            new_adviser = AdviserFactory()

            url = reverse('api-v4:task:item', kwargs={'pk': task.id})

            response = self.adviser_api_client(adviser).patch(
                url,
                data={'advisers': [new_adviser.id]},
            )
            assert response.status_code == status.HTTP_200_OK
            assert response.json()['advisers'][0]['id'] == str(new_adviser.id)

    class TestArchiveTask(BaseTaskTests):
        """Test the archive POST endpoint for task"""

        def test_archive_task_without_reason_returns_bad_request(self):
            adviser = AdviserFactory()
            task = TaskFactory(created_by=adviser)

            url = reverse('api-v4:task:task_archive', kwargs={'pk': task.id})

            response = self.adviser_api_client(adviser).post(url, data={})

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert response.data == {
                'reason': ['This field is required.'],
            }

        def test_archive_task_returns_forbidden_when_user_not_creator_or_assigned_to_task(self):
            task = TaskFactory()

            url = reverse('api-v4:task:task_archive', kwargs={'pk': task.id})

            response = self.api_client.post(url, data={'reason': 'completed'})

            assert response.status_code == status.HTTP_403_FORBIDDEN

        def test_archive_task_returns_success_when_user_is_creator_but_not_assigned_to_task(self):
            adviser = AdviserFactory()
            task = TaskFactory(created_by=adviser)

            url = reverse('api-v4:task:task_archive', kwargs={'pk': task.id})

            response = self.adviser_api_client(adviser).post(url, data={'reason': 'completed'})

            assert response.status_code == status.HTTP_200_OK

        def test_archive_task_returns_success_when_user_is_not_creator_but_is_assigned_to_task(
            self,
        ):
            adviser = AdviserFactory()
            task = TaskFactory(advisers=[adviser])

            url = reverse('api-v4:task:task_archive', kwargs={'pk': task.id})

            response = self.adviser_api_client(adviser).post(url, data={'reason': 'completed'})

            assert response.status_code == status.HTTP_200_OK

        def test_archive_task_returns_success_when_user_is_creator_and_is_assigned_to_task(self):
            adviser = AdviserFactory()
            task = TaskFactory(advisers=[adviser], created_by=adviser)

            url = reverse('api-v4:task:task_archive', kwargs={'pk': task.id})

            response = self.adviser_api_client(adviser).post(url, data={'reason': 'completed'})

            assert response.status_code == status.HTTP_200_OK

        def test_archive_task_with_valid_reason_returns_success(self):
            adviser = AdviserFactory()
            task = TaskFactory(created_by=adviser)
            url = reverse('api-v4:task:task_archive', kwargs={'pk': task.id})
            response = self.adviser_api_client(adviser).post(url, data={'reason': 'completed'})

            assert response.status_code == status.HTTP_200_OK
            assert response.data['archived']
            assert response.data['archived_by'] == {
                'id': str(adviser.id),
                'first_name': adviser.first_name,
                'last_name': adviser.last_name,
                'name': adviser.name,
            }
            assert response.data['archived_reason'] == 'completed'
            assert response.data['id'] == str(task.id)


class TestInvestmentProjectTaskV4ViewSet:
    class TestListInvestmentProjectTask(BaseListTaskTests):
        """Test the LIST investment project task endpoint"""

        reverse_url = 'api-v4:task:investment_project_task_collection'
        task_type_factory = InvestmentProjectTaskFactory

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
                "id": str(investment_task.id),
                "investment_project": {
                    "name": investment_task.investment_project.name,
                    "id": str(investment_task.investment_project.id),
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
