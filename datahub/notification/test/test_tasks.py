from unittest import mock

import pytest
from celery.exceptions import Retry
from notifications_python_client.errors import HTTPError

from datahub.notification import notify_gateway
from datahub.notification.constants import DEFAULT_SERVICE_NAME, NotifyServiceName
from datahub.notification.tasks import send_email_notification


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
    'error_status_code,expect_retry',
    (
        (503, True),
        (500, True),
        (403, False),
        (400, False),
    ),
)
def test_send_email_notification_retries_errors(monkeypatch, error_status_code, expect_retry):
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

    # Mock the task's retry method
    retry_mock = mock.Mock(side_effect=Retry())
    monkeypatch.setattr('datahub.notification.tasks.send_email_notification.retry', retry_mock)

    if expect_retry:
        expected_exception_class = Retry
    else:
        expected_exception_class = HTTPError

    with pytest.raises(expected_exception_class):
        send_email_notification('foobar@example.net', 'abcdefg')
