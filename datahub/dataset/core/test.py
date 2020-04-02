from unittest import mock

import pytest
from rest_framework import status


class BaseDatasetViewTest:
    """Base test class for dataset view tests.

    When subclassed by a view test class adds authentication and authorization
    tests common for all views.

    """

    view_url = None
    factory = None

    @pytest.mark.parametrize('method', ('delete', 'patch', 'post', 'put'))
    def test_other_methods_not_allowed(
        self,
        data_flow_api_client,
        method,
    ):
        """Test that various HTTP methods are not allowed."""
        response = data_flow_api_client.request(method, self.view_url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_without_scope(self, hawk_api_client):
        """Test that making a request without the correct Hawk scope returns an error."""
        hawk_api_client.set_credentials(
            'test-id-without-scope',
            'test-key-without-scope',
        )
        response = hawk_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_without_credentials(self, api_client):
        """Test that making a request without credentials returns an error."""
        response = api_client.get(self.view_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_without_whitelisted_ip(self, data_flow_api_client):
        """Test that making a request without the whitelisted IP returns an error."""
        data_flow_api_client.set_http_x_forwarded_for('1.1.1.1')
        response = data_flow_api_client.get(self.view_url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_no_data(self, data_flow_api_client):
        """Test that without any data available, endpoint completes the request successfully"""
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK

    @mock.patch('datahub.dataset.core.pagination.DatasetCursorPagination.page_size', 2)
    def test_pagination(self, data_flow_api_client):
        """Test that when page size higher than threshold response returns with next page url"""
        self.factory.create_batch(2 + 1)
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['next'] is not None

    def test_pagination_can_be_controlled_by_client(self, data_flow_api_client):
        """Test that pagination can be controlled by the client"""
        self.factory.create_batch(2)
        response_for_page_size_1 = data_flow_api_client.get(self.view_url, params={'page_size': 1})
        response_for_page_size_2 = data_flow_api_client.get(self.view_url, params={'page_size': 2})
        assert response_for_page_size_1.status_code == status.HTTP_200_OK
        assert response_for_page_size_2.status_code == status.HTTP_200_OK
        assert len(response_for_page_size_1.json()['results']) == 1
        assert len(response_for_page_size_2.json()['results']) == 2

    @mock.patch('datahub.dataset.core.pagination.DatasetCursorPagination.max_page_size', 2)
    def test_pagination_respects_max_page_size(self, data_flow_api_client):
        """Test that pagination conrolled by the client cannot bypass our own max page size"""
        self.factory.create_batch(2)
        response_for_page_size_1 = data_flow_api_client.get(self.view_url, params={'page_size': 1})
        response_for_page_size_10 = data_flow_api_client.get(
            self.view_url,
            params={'page_size': 10},
        )
        assert response_for_page_size_1.status_code == status.HTTP_200_OK
        assert response_for_page_size_10.status_code == status.HTTP_200_OK
        assert len(response_for_page_size_1.json()['results']) == 1
        assert len(response_for_page_size_10.json()['results']) == 2
