from unittest import mock

from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.test_utils import LeelooTestCase
from .factories import TaskInfoFactory


class TaskInfoTestCase(LeelooTestCase):
    """Task info testcase."""

    @mock.patch('datahub.core.models.tasks')
    def test_task_info_list_view(self, mocked_tasks_module):
        """List task info."""
        TaskInfoFactory(user=self.user)
        TaskInfoFactory(user=self.user)
        url = reverse('taskinfo-list')
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['count'] == 2
        assert 'status' in response.json()['results'][0].keys()
