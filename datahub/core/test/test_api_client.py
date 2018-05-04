import pytest
from requests import HTTPError
from requests.auth import HTTPBasicAuth

from datahub.core.api_client import APIClient


class TestAPIClient:
    """Tests APIClient."""

    def test_successful_request(self, requests_stubber):
        """Tests making a successful request."""
        api_url = 'http://test/v1/'
        requests_stubber.get('http://test/v1/path/to/item', status_code=200)

        api_client = APIClient(api_url)
        response = api_client.request('GET', 'path/to/item')

        assert response.status_code == 200
        assert response.request.headers['Accept'] == APIClient.DEFAULT_ACCEPT
        assert response.request.timeout is None

    def test_raises_exception_on_unsuccessful_request(self, requests_stubber):
        """Tests that an exception is raised on an successful request."""
        api_url = 'http://test/v1/'
        requests_stubber.get('http://test/v1/path/to/item', status_code=404)

        api_client = APIClient(api_url)
        with pytest.raises(HTTPError) as excinfo:
            api_client.request('GET', 'path/to/item')

        assert excinfo.value.response.status_code == 404

    def test_passes_through_arguments(self, requests_stubber):
        """Tests that auth, accept and default_timeout are passed to the request."""
        api_url = 'http://test/v1/'
        requests_stubber.get('http://test/v1/path/to/item', status_code=200)

        api_client = APIClient(
            api_url,
            auth=HTTPBasicAuth('user', 'password'),
            accept='test-accept',
            default_timeout=10,
        )
        response = api_client.request('GET', 'path/to/item')

        assert response.status_code == 200
        assert response.request.headers['Accept'] == 'test-accept'
        assert response.request.timeout == 10

    def test_omits_accept_if_none(self, requests_stubber):
        """Tests that the Accept header is not overridden when accept=None is passed."""
        api_url = 'http://test/v1/'
        requests_stubber.get('http://test/v1/path/to/item', status_code=200)

        api_client = APIClient(
            api_url,
            auth=HTTPBasicAuth('user', 'password'),
            accept=None,
        )
        response = api_client.request('GET', 'path/to/item')

        assert response.status_code == 200
        assert response.request.headers['Accept'] == '*/*'

    @pytest.mark.parametrize('default_timeout', (10, None))
    def test_can_override_timeout_per_request(self, requests_stubber, default_timeout):
        """Tests that the timeout can be overridden for a specific request."""
        api_url = 'http://test/v1/'
        requests_stubber.get('http://test/v1/path/to/item', status_code=200)

        api_client = APIClient(
            api_url,
            auth=HTTPBasicAuth('user', 'password'),
            accept='test-accept',
            default_timeout=default_timeout,
        )
        response = api_client.request('GET', 'path/to/item', timeout=20)

        assert response.status_code == 200
        assert response.request.headers['Accept'] == 'test-accept'
        assert response.request.timeout == 20
