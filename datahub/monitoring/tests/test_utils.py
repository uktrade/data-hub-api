import logging
from unittest.mock import Mock
from urllib.error import URLError

import pytest

from datahub.monitoring.utils import push_to_gateway


@pytest.fixture
def mock_push_to_gateway(monkeypatch):
    """
    Mocks the underlying library function.
    """
    mock_push_to_gateway = Mock()
    monkeypatch.setattr(
        'datahub.monitoring.utils._push_to_gateway',
        mock_push_to_gateway,
    )
    monkeypatch.setattr(
        'datahub.monitoring.utils.registry',
        'mock-registry',
    )
    return mock_push_to_gateway


@pytest.fixture
def mock_pushgateway_settings(monkeypatch):
    """
    Mocks PUSHGATEWAY_URL
    """
    mock_settings = Mock()
    mock_settings.PUSHGATEWAY_URL = 'http://example.com'
    monkeypatch.setattr(
        'datahub.monitoring.utils.settings',
        mock_settings,
    )
    return mock_settings


def test_push_to_gateway(
    mock_push_to_gateway,
    mock_pushgateway_settings,
):
    """
    Test push_to_gateway when everything is properly
    configured.
    """
    push_to_gateway('test-job')
    mock_push_to_gateway.assert_called_with(
        'http://example.com',
        job='test-job',
        registry='mock-registry',
    )


def test_push_to_gateway_no_url(mock_push_to_gateway, caplog):
    """
    Test push_to_gateway when PUSHGATEWAY_URL has not been
    configured.
    """
    with caplog.at_level(logging.INFO, logger='datahub.monitoring.utils'):
        push_to_gateway('test-job')
        assert caplog.messages == [
            'PUSHGATEWAY_URL has not been configured.',
        ]


def test_push_to_gateway_not_reachable(
    mock_push_to_gateway,
    mock_pushgateway_settings,
    caplog,
):
    """
    Test push_to_gateway when pushgateway cannot be reached.
    """
    mock_push_to_gateway.side_effect = URLError('Mock network error')
    with caplog.at_level(logging.INFO, logger='datahub.monitoring.utils'):
        push_to_gateway('test-job')
        assert caplog.messages == [
            'Cannot reach Pushgateway at: http://example.com',
        ]
