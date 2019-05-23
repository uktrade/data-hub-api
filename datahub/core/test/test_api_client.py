import re
from unittest.mock import Mock

import pytest
from freezegun import freeze_time
from requests import HTTPError
from requests.auth import HTTPBasicAuth

from datahub.core.api_client import APIClient, HawkAuth


class TestHawkAuth:
    """Tests HawkAuth."""

    @freeze_time('2018-01-01 00:00:00')
    def test_requests_with_no_body_are_signed(self):
        """Tests that requests without a body are signed."""
        auth = HawkAuth('test-id', 'test-key')
        request = Mock(method='GET', url='http://test.com/test', body=None, headers={})
        auth(request)

        pattern = re.compile('Hawk mac=".*", hash=".*", id="test-id", ts="1514764800", nonce=".*"')
        assert pattern.match(request.headers['Authorization'])

    def test_exception_raised_if_response_fails_verification(self, monkeypatch):
        """Test that responses are verified when response verification is enabled."""
        accept_response_mock = Mock(side_effect=ValueError())
        monkeypatch.setattr('mohawk.Sender.accept_response', accept_response_mock)

        auth = HawkAuth('test-id', 'test-key')
        request = Mock(method='GET', url='http://test.com/test', body=None, headers={})
        auth(request)

        request.register_hook.assert_called_once()
        response = Mock(
            content=b'',
            ok=True,
            headers={
                'Server-Authorization': 'test',
                'Content-Type': 'test/test',
            },
        )

        with pytest.raises(ValueError):
            request.register_hook.call_args[0][1](response)

    def test_response_not_verified_if_verification_disabled(self):
        """Test that responses are not verified when response verification is disabled."""
        auth = HawkAuth('test-id', 'test-key', verify_response=False)
        request = Mock(method='GET', url='http://test.com/test', body=None, headers={})
        auth(request)

        request.register_hook.assert_not_called()


class TestAPIClient:
    """Tests APIClient."""

    def test_successful_request(self, requests_mock):
        """Tests making a successful request."""
        api_url = 'http://test/v1/'
        requests_mock.get('http://test/v1/path/to/item', status_code=200)

        api_client = APIClient(api_url)
        response = api_client.request('GET', 'path/to/item')

        assert response.status_code == 200
        assert response.request.headers['Accept'] == APIClient.DEFAULT_ACCEPT
        assert response.request.timeout is None

    def test_raises_exception_on_unsuccessful_request_if_flag_is_true(self, requests_mock):
        """
        Tests that an exception is raised on an successful request
        if the raise_for_status argument is True.
        """
        api_url = 'http://test/v1/'
        requests_mock.get('http://test/v1/path/to/item', status_code=404)

        api_client = APIClient(api_url, raise_for_status=True)
        with pytest.raises(HTTPError) as excinfo:
            api_client.request('GET', 'path/to/item')

        assert excinfo.value.response.status_code == 404

    def test_doesnt_raise_exception_on_unsuccessful_request_if_flag_is_false(self, requests_mock):
        """
        Tests that no exception is raised on an successful request
        if the raise_for_status argument is False.
        """
        api_url = 'http://test/v1/'
        requests_mock.get('http://test/v1/path/to/item', status_code=404)

        api_client = APIClient(api_url, raise_for_status=False)
        response = api_client.request('GET', 'path/to/item')

        assert response.status_code == 404

    def test_passes_through_arguments(self, requests_mock):
        """Tests that auth, accept and default_timeout are passed to the request."""
        api_url = 'http://test/v1/'
        requests_mock.get('http://test/v1/path/to/item', status_code=200)

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

    def test_omits_accept_if_none(self, requests_mock):
        """Tests that the Accept header is not overridden when accept=None is passed."""
        api_url = 'http://test/v1/'
        requests_mock.get('http://test/v1/path/to/item', status_code=200)

        api_client = APIClient(
            api_url,
            auth=HTTPBasicAuth('user', 'password'),
            accept=None,
        )
        response = api_client.request('GET', 'path/to/item')

        assert response.status_code == 200
        assert response.request.headers['Accept'] == '*/*'

    @pytest.mark.parametrize('default_timeout', (10, None))
    def test_can_override_timeout_per_request(self, requests_mock, default_timeout):
        """Tests that the timeout can be overridden for a specific request."""
        api_url = 'http://test/v1/'
        requests_mock.get('http://test/v1/path/to/item', status_code=200)

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
