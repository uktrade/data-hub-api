import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import AdviserFactory
from datahub.core.test_utils import APITestMixin, create_test_user
from datahub.metadata.test.factories import TeamFactory
from datahub.search.task.apps import TaskSearchApp
from datahub.task.test.factories import InvestmentProjectTaskFactory, TaskFactory


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

        investment_project_task = InvestmentProjectTaskFactory(
            task=TaskFactory(
                advisers=[
                    adviser1,
                ],
            ),
        )
        InvestmentProjectTaskFactory()

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
        assert response.data['results'][0]['id'] == str(investment_project_task.task.id)

    def test_search_task_by_created_by_id(self, opensearch_with_collector):
        """Tests task search by created by id."""
        adviser1 = AdviserFactory()

        investment_project_task = InvestmentProjectTaskFactory(
            task=TaskFactory(
                created_by=adviser1,
            ),
        )
        InvestmentProjectTaskFactory()

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
        assert response.data['results'][0]['id'] == str(investment_project_task.task.id)

    def test_search_task_by_archived(self, opensearch_with_collector):
        """Tests task search by archived."""
        archived_investment_project_task = InvestmentProjectTaskFactory(
            task=TaskFactory(archived=True),
        )
        InvestmentProjectTaskFactory(
            task=TaskFactory(archived=False),
        )

        opensearch_with_collector.flush_and_refresh()

        url = reverse('api-v4:search:task')

        response = self.api_client.post(
            url,
            data={
                'archived': True,
            },
        )

        assert response.status_code == status.HTTP_200_OK

        assert response.data['count'] == 1
        assert response.data['results'][0]['id'] == str(archived_investment_project_task.task.id)
