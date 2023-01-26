from unittest import mock

import pytest
from notifications_python_client.errors import HTTPError

from datahub.notification import notify_gateway
from datahub.notification.constants import DEFAULT_SERVICE_NAME, NotifyServiceName
from datahub.notification.tasks import send_email_notification


@pytest.fixture()
def mock_rq_get_current_job(monkeypatch):
    mock_notification_tasks_get_current_job = mock.Mock()
    monkeypatch.setattr(
        'datahub.notification.tasks.get_current_job',
        mock_notification_tasks_get_current_job,
    )
    mock_notification_tasks_get_current_job.retries_left = 5
    return mock_notification_tasks_get_current_job


@pytest.mark.parametrize(
    'context,service_name',
    (
        (None, None),
        ({'foo': 'bar'}, None),
        ({'foo': 'bar'}, NotifyServiceName.omis),
    ),
)
def test_send_email_notification(context, service_name):
    """
    Test the send_email_notification utility.
    """
    expected_service_name = service_name or DEFAULT_SERVICE_NAME
    notification_api_client = notify_gateway.clients[expected_service_name]
    notification_api_client.send_email_notification.return_value = {'id': 'someid'}
    notification_id = send_email_notification(
        'foobar@example.net',
        'abcdefg',
        context,
        service_name,
    )
    assert notification_id == 'someid'
    notification_api_client.send_email_notification.assert_called_with(
        email_address='foobar@example.net',
        template_id='abcdefg',
        personalisation=context or {},
    )


@pytest.mark.parametrize(
    'error_status_code,expect_retry,get_current_job_return_none',
    (
        (503, True, False),
        (500, True, False),
        (403, False, False),
        (400, False, False),
        (400, False, True),
    ),
)
def test_send_email_notification_retries_errors(
        monkeypatch,
        mock_rq_get_current_job,
        error_status_code,
        expect_retry,
        get_current_job_return_none,
):
    """
    Test the send_email_notification utility.
    """
    notification_api_client = notify_gateway.clients[DEFAULT_SERVICE_NAME]
    # Set up an HTTPError with the parametrized status code
    mock_response = mock.Mock()
    mock_response.status_code = error_status_code
    mock_response.json.return_value = {}
    error = HTTPError(mock_response)
    notification_api_client.send_email_notification.side_effect = error

    if get_current_job_return_none:
        mock_rq_get_current_job.return_value = None

    with pytest.raises(HTTPError):
        send_email_notification('foobar@example.net', 'abcdefg')

    if expect_retry:
        # Don't expect get_current_job called
        assert mock_rq_get_current_job.call_count == 0
    else:
        # Expect get_current_job called
        assert mock_rq_get_current_job.call_count == 1
        if get_current_job_return_none:
            assert mock_rq_get_current_job.return_value is None
        else:
            assert mock_rq_get_current_job.return_value.retries_left == 0
