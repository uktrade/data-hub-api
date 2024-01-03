import datetime

from operator import attrgetter

from uuid import uuid4

import factory

import pytest

from django.utils.timezone import now

from faker import Faker

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from datahub.company.test.factories import AdviserFactory, CompanyFactory
from datahub.core.test_utils import (
    APITestMixin,
    format_date_or_datetime,
)
from datahub.interaction.test.factories import InteractionFactoryBase
from datahub.investment.project.test.factories import InvestmentProjectFactory

from datahub.task.test.factories import TaskFactory
from datahub.task.test.utils import BaseEditTaskTests, BaseListTaskTests, BaseTaskTests


class TestListTask(BaseListTaskTests):
    """Test the LIST task endpoint"""

    reverse_url = 'api-v4:task:collection'

    def test_get_all_tasks_returns_ordered_results_when_sortby_param_is_used(self):
        earliest_task = TaskFactory(due_date=datetime.date.today() - datetime.timedelta(days=1))
        latest_task = TaskFactory(due_date=datetime.date.today() + datetime.timedelta(days=1))
        middle_task = TaskFactory(due_date=datetime.date.today())

        url = f'{reverse(self.reverse_url)}?sortby=due_date'

        response = self.api_client.get(url).json()

        ordered_ids_response = [result['id'] for result in response['results']]
        assert ordered_ids_response == [
            str(earliest_task.id),
            str(middle_task.id),
            str(latest_task.id),
        ]

    def test_returns_only_tasks_with_investment_project_when_param_is_used(self):
        investment_projects = InvestmentProjectFactory.create_batch(2)
        TaskFactory.create_batch(3)
        TaskFactory.create_batch(2, investment_project=investment_projects[0])
        TaskFactory.create_batch(3, investment_project=investment_projects[1])

        url = f'{reverse(self.reverse_url)}?investment_project={investment_projects[0].id}'

        response = self.api_client.get(url).json()

        assert response.get('count') == 2

    def test_returns_only_tasks_with_company_when_param_is_used(self):
        companies = CompanyFactory.create_batch(2)

        TaskFactory.create_batch(3)
        TaskFactory.create_batch(2, company=companies[0])
        TaskFactory.create_batch(3, company=companies[1])

        url = f'{reverse(self.reverse_url)}?company={companies[0].id}'

        response = self.api_client.get(url).json()

        assert response.get('count') == 2


class TestGetGenericTask(APITestMixin):
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
            'modified_on': format_date_or_datetime(task.modified_on),
            'investment_project': None,
            'company': None,
            'interaction': None,
        }
        assert response == expected_response


class TestAddGenericTask(APITestMixin):
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

    def test_create_task_with_empty_advisors_returns_bad_request(self):
        faker = Faker()

        url = reverse('api-v4:task:collection')

        response = self.api_client.post(
            url,
            data={'title': faker.word(), 'advisers': []},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert list(response.json().keys()) == ['advisers']

    def test_create_task_with_multiple_relationships_returns_error(self):
        url = reverse('api-v4:task:collection')
        faker = Faker()

        company = CompanyFactory()
        investment_project = InvestmentProjectFactory()
        interaction = InteractionFactoryBase()
        adviser = AdviserFactory()

        response = self.api_client.post(
            url,
            data={
                'title': faker.word(),
                'advisers': [adviser.id],
                'company': company.id,
                'investment_project': investment_project.id,
                'interaction': interaction.id,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert list(response.json().keys()) == ['non_field_errors']

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
            'modified_on': post_response_json['modified_on'],
            'investment_project': None,
            'company': None,
            'interaction': None,
        }
        assert get_response.json() == expected_response


class TestEditGenericTask(BaseEditTaskTests):
    reverse_url = 'api-v4:task:item'

    """Test the PATCH task endpoint"""

    def test_edit_task_return_404_when_task_id_unknown(self):
        url = reverse('api-v4:task:item', kwargs={'pk': uuid4()})

        response = self.api_client.patch(
            url,
            data={'title': 'abc'},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

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


class TestTaskForInvestmentProject(APITestMixin):
    @pytest.mark.parametrize('investment_project_id', ('abc', uuid4()))
    def test_create_task_with_invalid_investment_project_id_returns_bad_request(
        self,
        investment_project_id,
    ):
        faker = Faker()

        url = reverse('api-v4:task:collection')

        response = self.api_client.post(
            url,
            data={
                'title': faker.word(),
                'advisers': [AdviserFactory().id],
                'investment_project': investment_project_id,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        assert list(response.json().keys()) == ['investment_project']

    def test_create_task_with_valid_investment_project_id_returns_success(
        self,
    ):
        faker = Faker()

        url = reverse('api-v4:task:collection')

        response = self.api_client.post(
            url,
            data={
                'title': faker.word(),
                'advisers': [AdviserFactory().id],
                'investment_project': InvestmentProjectFactory().id,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED

    def test_get_task_with_investment_project_when_task_id_valid(self):
        investment_project = InvestmentProjectFactory()
        task = TaskFactory(investment_project=investment_project)

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
            'modified_on': format_date_or_datetime(task.modified_on),
            'investment_project': {
                'name': investment_project.name,
                'id': str(investment_project.id),
                'investor_company': {
                    'name': investment_project.investor_company.name,
                    'id': str(investment_project.investor_company.id),
                },
                'project_code': investment_project.project_code,
            },
            'company': {
                'id': str(investment_project.investor_company.id),
                'name': investment_project.investor_company.name,
            },
            'interaction': None,
        }
        assert response == expected_response


class TestTaskForCompany(APITestMixin):
    @pytest.mark.parametrize('company_id', ('abc', uuid4()))
    def test_create_task_with_invalid_company_id_returns_bad_request(
        self,
        company_id,
    ):
        faker = Faker()

        url = reverse('api-v4:task:collection')

        response = self.api_client.post(
            url,
            data={
                'title': faker.word(),
                'advisers': [AdviserFactory().id],
                'company': company_id,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        assert list(response.json().keys()) == ['company']

    def test_create_task_with_valid_company_id_returns_success(
        self,
    ):
        faker = Faker()

        url = reverse('api-v4:task:collection')

        response = self.api_client.post(
            url,
            data={
                'title': faker.word(),
                'advisers': [AdviserFactory().id],
                'company': CompanyFactory().id,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED

    def test_get_task_with_company_when_task_id_valid(self):
        company = CompanyFactory()
        task = TaskFactory(company=company)

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
            'modified_on': format_date_or_datetime(task.modified_on),
            'investment_project': None,
            'company': {
                'id': str(company.id),
                'name': company.name,
            },
            'interaction': None,
        }
        assert response == expected_response


class TestTaskForInteraction(APITestMixin):
    @pytest.mark.parametrize('interaction_id', ('abc', uuid4()))
    def test_create_task_with_invalid_interaction_id_returns_bad_request(
        self,
        interaction_id,
    ):
        faker = Faker()

        url = reverse('api-v4:task:collection')

        response = self.api_client.post(
            url,
            data={
                'title': faker.word(),
                'advisers': [AdviserFactory().id],
                'interaction': interaction_id,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        assert list(response.json().keys()) == ['interaction']

    def test_create_task_with_valid_interaction_id_returns_success(
        self,
    ):
        faker = Faker()

        url = reverse('api-v4:task:collection')

        response = self.api_client.post(
            url,
            data={
                'title': faker.word(),
                'advisers': [AdviserFactory().id],
                'interaction': InteractionFactoryBase().id,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED

    def test_get_task_with_interaction_when_task_id_valid(self):
        interaction = InteractionFactoryBase()
        task = TaskFactory(interaction=interaction)

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
            'modified_on': format_date_or_datetime(task.modified_on),
            'investment_project': None,
            'company': {
                'id': str(interaction.company.id),
                'name': interaction.company.name,
            },
            'interaction': {'id': str(interaction.id), 'subject': interaction.subject},
        }
        assert response == expected_response


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

    def test_archive_task_returns_unauthorized_when_user_not_authenticated(self):
        adviser = AdviserFactory()
        task = TaskFactory(advisers=[adviser])

        url = reverse('api-v4:task:task_archive', kwargs={'pk': task.id})

        response = APIClient().post(url, data={'reason': 'completed'})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

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


class TestAssociatedCompanyAndProject(APITestMixin):
    """Test the GET companies-and-projects endpoint for task"""

    url = reverse('api-v4:task:companies-and-projects')

    def test_returns_empty_when_no_companies_or_projects(self):
        TaskFactory()

        response = self.api_client.get(self.url).json()
        expected_response = {
            'companies': [],
            'projects': [],
        }

        assert response == expected_response

    def test_returns_project_investor_company_in_company_field(self):
        company = CompanyFactory()
        project = InvestmentProjectFactory()
        TaskFactory(created_by=self.user, company=company)
        TaskFactory(created_by=self.user, investment_project=project)

        response = self.api_client.get(self.url).json()

        sorted_companies = [company, project.investor_company]
        sorted_companies.sort(key=attrgetter('name'))

        expected_response = {
            'companies': [
                {
                    'id': str(company.id),
                    'name': company.name,
                }
                for company in sorted_companies
            ],
            'projects': [
                {
                    'id': str(project.id),
                    'name': project.name,
                },
            ],
        }

        assert response == expected_response

    def test_returns_company_once_when_multiple_tasks_with_same_company(self):
        company = CompanyFactory()
        TaskFactory.create_batch(2, created_by=self.user, company=company)

        response = self.api_client.get(self.url).json()
        expected_response = {
            'companies': [
                {
                    'id': str(company.id),
                    'name': company.name,
                },
            ],
            'projects': [],
        }

        assert response == expected_response

    def test_returns_project_once_when_multiple_tasks_with_same_project(self):
        project = InvestmentProjectFactory()
        TaskFactory.create_batch(2, created_by=self.user, investment_project=project)

        response = self.api_client.get(self.url).json()
        expected_response = {
            'companies': [
                {
                    'id': str(project.investor_company.id),
                    'name': project.investor_company.name,
                },
            ],
            'projects': [
                {
                    'id': str(project.id),
                    'name': project.name,
                },
            ],
        }

        assert response == expected_response

    def test_returns_multiple_companies_and_projects_for_tasks(self):
        companies = CompanyFactory.create_batch(
            2,
            name=factory.Iterator(
                ('Company A', 'Company B'),
            ),
        )

        projects = InvestmentProjectFactory.create_batch(
            2,
            name=factory.Iterator(
                ('Project A', 'Project B'),
            ),
        )

        TaskFactory.create_batch(
            2,
            created_by=self.user,
            company=factory.Iterator(companies),
        )
        TaskFactory.create_batch(
            2,
            created_by=self.user,
            investment_project=factory.Iterator(projects),
        )

        response = self.api_client.get(self.url).json()

        sorted_companies = companies + [project.investor_company for project in projects]
        sorted_companies.sort(key=attrgetter('name'))

        expected_response = {
            'companies': [
                {
                    'id': str(company.id),
                    'name': company.name,
                }
                for company in sorted_companies
            ],
            'projects': [
                {
                    'id': str(project.id),
                    'name': project.name,
                }
                for project in projects
            ],
        }

        assert response == expected_response
