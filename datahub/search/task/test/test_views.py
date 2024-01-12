from datetime import datetime, timedelta
from unittest import mock

import pytest

from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import AdviserFactory, CompanyFactory
from datahub.core.test_utils import APITestMixin, create_test_user
from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.metadata.test.factories import TeamFactory
from datahub.search.task.apps import TaskSearchApp
from datahub.task.test.factories import TaskFactory


pytestmark = [
    pytest.mark.django_db,
    # Index objects for this search app only
    pytest.mark.opensearch_collector_apps.with_args(TaskSearchApp),
]


class TestTaskSearch(APITestMixin):
    """Tests task search views."""

    def test_task_search_no_permissions(self):
        """Should return 403"""
        user = create_test_user(dit_team=TeamFactory())
        api_client = self.create_api_client(user=user)
        url = reverse('api-v4:search:task')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_search_task_by_advisor_id(self, opensearch_with_collector):
        """Tests task search by advisor id."""
        adviser1 = AdviserFactory()

        task = TaskFactory(
            advisers=[
                adviser1.id,
                self.user.id,
            ],
        )

        TaskFactory()

        opensearch_with_collector.flush_and_refresh()

        url = reverse('api-v4:search:task')

        response = self.api_client.post(
            url,
            data={
                'advisers': [adviser1.id],
            },
        )

        assert response.status_code == status.HTTP_200_OK

        assert response.data['count'] == 1
        assert response.data['results'][0]['id'] == str(task.id)

    def test_search_task_by_created_by_id(self, opensearch_with_collector):
        """Tests task search by created by id."""
        adviser1 = AdviserFactory()
        adviser1.id = self.user.id

        task = TaskFactory(
            created_by=adviser1,
        )

        TaskFactory()

        opensearch_with_collector.flush_and_refresh()

        url = reverse('api-v4:search:task')

        response = self.api_client.post(
            url,
            data={
                'created_by': adviser1.id,
            },
        )

        assert response.status_code == status.HTTP_200_OK

        assert response.data['count'] == 1
        assert response.data['results'][0]['id'] == str(task.id)

    def test_search_task_not_created_by_id(self, opensearch_with_collector):
        """Tests task search by not created by id."""
        created_by_adviser = AdviserFactory()
        not_created_by_adviser = AdviserFactory()

        task = TaskFactory(
            created_by=created_by_adviser,
            advisers=[self.user.id],
        )
        TaskFactory(
            created_by=not_created_by_adviser,
            advisers=[self.user.id],
        )

        opensearch_with_collector.flush_and_refresh()

        url = reverse('api-v4:search:task')

        response = self.api_client.post(
            url,
            data={
                'not_created_by': not_created_by_adviser.id,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['id'] == str(task.id)
        assert response.data['results'][0]['created_by']['id'] == str(created_by_adviser.id)

    def test_search_task_not_created_by_id_works_in_combination_with_other_parameters(
        self,
        opensearch_with_collector,
    ):
        """
        Tests task not created by id filter works in combination with other parameters.
        We're testing this with an adviser.
        """
        created_by_adviser = AdviserFactory()
        not_created_by_adviser = AdviserFactory()
        adviser1 = AdviserFactory()
        adviser1.id = self.user.id

        task = TaskFactory(
            created_by=created_by_adviser,
            advisers=[
                adviser1,
            ],
        )
        TaskFactory(
            created_by=not_created_by_adviser,
            advisers=[
                adviser1,
            ],
        )
        TaskFactory(
            created_by=not_created_by_adviser,
        )
        TaskFactory()

        opensearch_with_collector.flush_and_refresh()

        url = reverse('api-v4:search:task')

        response = self.api_client.post(
            url,
            data={
                'not_created_by': not_created_by_adviser.id,
                'advisers': [adviser1.id],
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['id'] == str(task.id)

    def test_search_task_not_advisers(self, opensearch_with_collector):
        """Tests task search by not advisers id."""
        advisers = AdviserFactory.create_batch(2)
        not_advisers = AdviserFactory.create_batch(3)
        current_adviser = AdviserFactory()
        current_adviser.id = self.user.id

        task = TaskFactory(
            created_by=current_adviser,
            advisers=advisers,
        )
        TaskFactory(
            created_by=current_adviser,
            advisers=not_advisers,
        )
        TaskFactory(
            created_by=current_adviser,
            advisers=not_advisers + advisers,
        )
        # Task not assigned to or created by current adviser shouldn't be returned.
        TaskFactory(
            advisers=not_advisers + advisers,
        )

        opensearch_with_collector.flush_and_refresh()

        url = reverse('api-v4:search:task')

        response = self.api_client.post(
            url,
            data={'not_advisers': [not_adviser.id for not_adviser in not_advisers]},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['id'] == str(task.id)
        assert len(response.data['results'][0]['advisers']) == 2
        assert {
            response.data['results'][0]['advisers'][0]['id'],
            response.data['results'][0]['advisers'][1]['id'],
        } == {
            str(advisers[0].id),
            str(advisers[1].id),
        }

    @mock.patch('datahub.search.task.views.SearchTaskAPIView.deep_get')
    def test_search_task_without_filters(
        self,
        deep_get,
        opensearch_with_collector,
    ):
        """
        Tests edge case where no filter returned from raw_query
        """
        deep_get.return_value = None

        current_adviser = AdviserFactory()
        current_adviser.id = self.user.id

        TaskFactory(created_by=current_adviser)

        opensearch_with_collector.flush_and_refresh()

        url = reverse('api-v4:search:task')

        response = self.api_client.post(
            url,
        )

        assert response.status_code == status.HTTP_200_OK

        assert response.data['count'] == 1

    @mock.patch('datahub.search.task.views.SearchTaskAPIView.deep_get')
    def test_search_task_without_filter_index(
        self,
        deep_get,
        opensearch_with_collector,
    ):
        """
        Test edge case where no filter_index found in raw_query filter
        """
        not_created_by_adviser = AdviserFactory()
        deep_get.return_value = [{}]
        TaskFactory(
            advisers=[self.user.id],
        )

        opensearch_with_collector.flush_and_refresh()

        url = reverse('api-v4:search:task')

        response = self.api_client.post(
            url,
            data={
                'not_created_by': not_created_by_adviser.id,
            },
        )

        assert response.status_code == status.HTTP_200_OK

        assert response.data['count'] == 1

    @pytest.mark.parametrize('sort_order, expected_order', [('asc', [0, 1]), ('desc', [1, 0])])
    def test_search_task_due_date_ordering(
        self,
        opensearch_with_collector,
        sort_order,
        expected_order,
    ):
        """Tests task search ordering on due date"""
        current_adviser = AdviserFactory()
        current_adviser.id = self.user.id

        yesterday_task = TaskFactory(
            due_date=datetime.today() - timedelta(days=1),
            created_by=current_adviser,
        )
        today_task = TaskFactory(due_date=datetime.today(), created_by=current_adviser)

        opensearch_with_collector.flush_and_refresh()

        url = reverse('api-v4:search:task')

        response = self.api_client.post(
            url,
            data={
                'sortby': f'due_date:{sort_order}',
            },
        )

        assert response.status_code == status.HTTP_200_OK

        assert response.data['results'][expected_order[0]]['id'] == str(yesterday_task.id)
        assert response.data['results'][expected_order[1]]['id'] == str(today_task.id)

    @pytest.mark.parametrize('sort_order, expected_order', [('asc', [0, 1]), ('desc', [1, 0])])
    def test_search_task_company_name_ordering(
        self,
        opensearch_with_collector,
        sort_order,
        expected_order,
    ):
        """Tests task search ordering on company name"""
        company1 = CompanyFactory(name='Apple')
        company2 = CompanyFactory(name='Zebra')

        current_adviser = AdviserFactory()
        current_adviser.id = self.user.id

        first_task = TaskFactory(company=company1, created_by=current_adviser)
        second_task = TaskFactory(company=company2, created_by=current_adviser)

        opensearch_with_collector.flush_and_refresh()

        url = reverse('api-v4:search:task')

        response = self.api_client.post(
            url,
            data={
                'sortby': f'company.name:{sort_order}',
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'][expected_order[0]]['id'] == str(first_task.id)
        assert response.data['results'][expected_order[1]]['id'] == str(second_task.id)

    def test_search_task_company_name_ordering_puts_tasks_without_company_name_at_end(
        self,
        opensearch_with_collector,
    ):
        """Tests task search ordering on company name puts companies with a name first"""
        company1 = CompanyFactory(name='Apple')
        company2 = CompanyFactory(name='Zebra')

        current_adviser = AdviserFactory()
        current_adviser.id = self.user.id

        company_task_1 = TaskFactory(company=company1, created_by=current_adviser)
        company_task_2 = TaskFactory(company=company2, created_by=current_adviser)
        generic_task = TaskFactory(created_by=current_adviser)

        opensearch_with_collector.flush_and_refresh()

        url = reverse('api-v4:search:task')

        response = self.api_client.post(
            url,
            data={
                'sortby': 'company.name:asc',
            },
        )

        assert response.status_code == status.HTTP_200_OK

        assert response.data['results'][0]['id'] == str(company_task_1.id)
        assert response.data['results'][1]['id'] == str(company_task_2.id)
        assert response.data['results'][2]['id'] == str(generic_task.id)

    @pytest.mark.parametrize('sort_order, expected_order', [('asc', [0, 1]), ('desc', [1, 0])])
    def test_search_task_investment_project_name_ordering(
        self,
        opensearch_with_collector,
        sort_order,
        expected_order,
    ):
        """Tests task search ordering on investment project name"""
        investment_project1 = InvestmentProjectFactory(name='Apple')
        investment_project2 = InvestmentProjectFactory(name='Zebra')

        current_adviser = AdviserFactory()
        current_adviser.id = self.user.id

        first_task = TaskFactory(
            investment_project=investment_project1,
            created_by=current_adviser,
        )
        second_task = TaskFactory(
            investment_project=investment_project2,
            created_by=current_adviser,
        )

        opensearch_with_collector.flush_and_refresh()

        url = reverse('api-v4:search:task')

        response = self.api_client.post(
            url,
            data={
                'sortby': f'investment_project.name:{sort_order}',
            },
        )

        assert response.status_code == status.HTTP_200_OK

        assert response.data['results'][expected_order[0]]['id'] == str(first_task.id)
        assert response.data['results'][expected_order[1]]['id'] == str(second_task.id)


class TestTaskInvestmentProjectSearch(APITestMixin):
    def test_search_task_by_created_by_id(self, opensearch_with_collector):
        """Tests task search by created by id."""
        adviser1 = AdviserFactory()
        adviser1.id = self.user.id

        investment_project = InvestmentProjectFactory()
        TaskFactory(
            created_by=adviser1,
            investment_project=investment_project,
        )

        TaskFactory()

        opensearch_with_collector.flush_and_refresh()

        url = reverse('api-v4:search:task')

        response = self.api_client.post(
            url,
            data={
                'created_by': adviser1.id,
            },
        )

        assert response.status_code == status.HTTP_200_OK

        assert response.data['count'] == 1
        assert response.data['results'][0]['investment_project'] == {
            'name': investment_project.name,
            'id': str(investment_project.id),
            'project_code': investment_project.project_code,
        }
        assert response.data['results'][0]['company'] == {
            'name': investment_project.investor_company.name,
            'id': str(investment_project.investor_company.id),
        }

    @pytest.mark.parametrize('archived', (True, False))
    def test_search_task_by_archived(self, opensearch_with_collector, archived):
        """Tests task search by archived."""
        current_adviser = AdviserFactory()
        current_adviser.id = self.user.id

        archived_tasks = TaskFactory.create_batch(3, archived=True, created_by=current_adviser)

        not_archived_tasks = TaskFactory.create_batch(
            2,
            archived=False,
            created_by=current_adviser,
        )

        opensearch_with_collector.flush_and_refresh()

        url = reverse('api-v4:search:task')

        response = self.api_client.post(
            url,
            data={
                'archived': archived,
            },
        )

        tasks_for_assert = archived_tasks if archived else not_archived_tasks

        assert response.status_code == status.HTTP_200_OK

        assert [a['id'] for a in response.json()['results']] == [
            str(a.id) for a in sorted(tasks_for_assert, key=lambda x: x.id)
        ]

        assert response.data['count'] == len(
            tasks_for_assert,
        )

    @pytest.mark.parametrize('archived', (True, False))
    def test_search_task_by_archived_for_current_adviser(
        self,
        opensearch_with_collector,
        archived,
    ):
        """
        Only return tasks created by the current adviser or where they have been assigned as an
        adviser even if there additional filters added. This tests uses archived for this.
        """
        current_adviser = AdviserFactory()
        current_adviser.id = self.user.id

        TaskFactory.create_batch(2, archived=True)
        TaskFactory.create_batch(2, archived=False)

        archived_tasks = TaskFactory.create_batch(3, archived=True)
        archived_tasks[0].created_by = current_adviser
        archived_tasks[1].created_by = current_adviser
        archived_tasks[1].advisers.add(current_adviser)
        archived_tasks[2].advisers.add(current_adviser)
        [archived_task.save() for archived_task in archived_tasks]

        not_archived_tasks = TaskFactory.create_batch(2, archived=False)
        not_archived_tasks[0].created_by = current_adviser
        not_archived_tasks[1].advisers.add(current_adviser)
        [not_archived_task.save() for not_archived_task in not_archived_tasks]

        opensearch_with_collector.flush_and_refresh()

        url = reverse('api-v4:search:task')

        response = self.api_client.post(
            url,
            data={
                'archived': archived,
            },
        )

        tasks_for_assert = archived_tasks if archived else not_archived_tasks

        assert response.status_code == status.HTTP_200_OK

        assert [a['id'] for a in response.json()['results']] == [
            str(a.id) for a in sorted(tasks_for_assert, key=lambda x: x.id)
        ]

        assert response.data['count'] == len(
            tasks_for_assert,
        )
