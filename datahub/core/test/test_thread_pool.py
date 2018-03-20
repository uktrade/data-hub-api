from unittest import mock

import pytest

from datahub.core.thread_pool import submit_to_thread_pool

pytestmark = pytest.mark.django_db


def _synchronous_executor_submit(fn, *args, **kwargs):
    fn(*args, **kwargs)


@mock.patch('datahub.core.thread_pool._executor.submit', _synchronous_executor_submit)
@mock.patch('datahub.core.thread_pool.client')
def test_error_raises_exception(mock_raven_client):
    """
    Test that if an error occurs whilst executing a thread pool task,
    the exception is raised and sent to sentry.
    """
    mock_task = mock.Mock(__name__='mock_task', side_effect=ValueError())

    with pytest.raises(ValueError):
        submit_to_thread_pool(mock_task)

    assert mock_raven_client.captureException.called
