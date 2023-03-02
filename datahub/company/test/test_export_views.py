import pytest

from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import (
    ExportFactory,
)
from datahub.core.test_utils import APITestMixin

# mark the whole module for db use
pytestmark = pytest.mark.django_db


class TestListExport(APITestMixin):
    """Test the LIST export endpoint"""

    def test_list_without_pagination_success(self):
        """
        Test a request without any pagination criteria returns all stored exports in the response
        """
        ExportFactory.create_batch(20)
        url = reverse('api-v4:export:collection')
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['count'] == 20

    @pytest.mark.parametrize(
        'batch_size,offset,limit,expected_count',
        (
            (5, 0, 5, 5),
            (5, 3, 10, 2),
            (2, 2, 1, 0),
        ),
    )
    def test_list_with_pagination_success(self, batch_size, offset, limit, expected_count):
        """
        Test a request with pagination criteria returns expected export results
        """
        ExportFactory.create_batch(batch_size)

        url = reverse('api-v4:export:collection')
        response = self.api_client.get(
            url,
            data={
                'limit': limit,
                'offset': offset,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['count'] == batch_size
        assert len(response.json()['results']) == expected_count
