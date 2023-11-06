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
            str(a.task.id) for a in sorted(tasks_for_assert, key=lambda x: x.task.id)
        ]

        assert response.data['count'] == len(
            tasks_for_assert,
        )
