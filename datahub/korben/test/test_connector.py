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
