from unittest.mock import call, MagicMock, Mock

import pytest

from datahub.core.queues.retry import retry_with_backoff


def test_retry_with_backoff_and_then_error(monkeypatch):
    sleep_mock = MagicMock()
    monkeypatch.setattr('datahub.core.queues.retry.time', sleep_mock)
    retry_mock = Mock(side_effect=Exception('Crash to force retry'))
    retries = 10
    original_call = 1

    with pytest.raises(Exception):
        retry_with_backoff(
            fn=retry_mock,
            retries=retries,
            backoff_in_seconds=1,
        )

    assert retry_mock.call_count == original_call + retries
    assert sleep_mock.sleep.call_count == retries
    assert sleep_mock.sleep.call_args_list == [
        call(1),
        call(2),
        call(4),
        call(8),
        call(16),
        call(32),
        call(64),
        call(128),
        call(256),
        call(512),
    ]
