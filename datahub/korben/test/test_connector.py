from unittest import mock

import requests

from datahub.korben.connector import KorbenConnector


def test_handle_host():
    """Test handle host."""
    connector = KorbenConnector()
    assert connector.handle_host('foo') == 'http://foo'


def test_handle_host_with_protocol():
    """Test handle host with protocol."""
    connector = KorbenConnector()
    assert connector.handle_host('https://foo') == 'https://foo'


@mock.patch('datahub.korben.connector.requests')
def test_ping(mocked_requests):
    """Ping Korben."""
    mocked_requests.get.return_value = 'foo'
    connector = KorbenConnector()
    assert connector.ping() == 'foo'


@mock.patch('datahub.korben.connector.requests.get', side_effect=requests.exceptions.RequestException)
def test_ping_exception(mocked_get):
    """Ping Korben exception."""
    connector = KorbenConnector()
    assert connector.ping() is False


@mock.patch('datahub.korben.connector.requests')
def test_validate_credentials(mocked_requests):
    """Test validate credentials."""
    mocked_response = mock.Mock()
    mocked_response.json.return_value = 'True'
    mocked_requests.post.return_value = mocked_response
    connector = KorbenConnector()
    assert connector.validate_credentials('foo', 'bar') == 'True'


@mock.patch('datahub.korben.connector.requests.post', side_effect=requests.exceptions.RequestException)
def test_validate_credential_request_exception(mocked_post):
    """Ping Korben exception."""
    connector = KorbenConnector()
    assert connector.validate_credentials('foo', 'bar') is False


@mock.patch('datahub.korben.connector.requests.post', side_effect=ValueError)
def test_validate_credential_valueerror_exception(mocked_post):
    """Ping Korben exception."""
    connector = KorbenConnector()
    assert connector.validate_credentials('foo', 'bar') is False
