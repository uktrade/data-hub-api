from datetime import datetime, timedelta
from unittest import mock

import pytest

from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import AdviserFactory
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
                adviser1,
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
        )
        TaskFactory(
            created_by=not_created_by_adviser,
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

        task = TaskFactory(
            advisers=advisers,
        )
        TaskFactory(
            advisers=not_advisers,
        )
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
        assert set(
            [
                response.data['results'][0]['advisers'][0]['id'],
                response.data['results'][0]['advisers'][1]['id'],
            ],
        ) == set(
            [
                str(advisers[0].id),
                str(advisers[1].id),
            ],
        )

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
        TaskFactory()

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
        deep_get.return_value = [{'result': 'testing'}]
        TaskFactory()

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

    def test_search_task_due_date_ordering(self, opensearch_with_collector):
        """Tests task search ordering on due date"""
        yesterday_task = TaskFactory(due_date=datetime.today() - timedelta(days=1))
        today_task = TaskFactory(due_date=datetime.today())

        opensearch_with_collector.flush_and_refresh()

        url = reverse('api-v4:search:task')

        response = self.api_client.post(
            url,
            data={
                'sortby': 'due_date',
            },
        )

        assert response.status_code == status.HTTP_200_OK

        assert set(
            [
                response.data['results'][0]['id'],
                response.data['results'][1]['id'],
            ]
        ) == set([str(yesterday_task.id), str(today_task.id)])


class TestTaskInvestmentProjectSearch(APITestMixin):
    def test_search_task_by_created_by_id(self, opensearch_with_collector):
        """Tests task search by created by id."""
        adviser1 = AdviserFactory()
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
        archived_tasks = TaskFactory.create_batch(3, archived=True)

        not_archived_tasks = TaskFactory.create_batch(2, archived=False)

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
