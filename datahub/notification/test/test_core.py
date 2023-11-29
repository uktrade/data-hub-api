from uuid import uuid4

import pytest

from datahub.notification import notify_gateway
from datahub.notification.constants import DEFAULT_SERVICE_NAME, NotifyServiceName


@pytest.mark.parametrize(
    'context,service_name',
    (
        (None, None),
        ({'foo': 'bar'}, None),
        ({'foo': 'bar'}, NotifyServiceName.omis),
        ({'foo': 'bar'}, NotifyServiceName.investment),
        ({'foo': 'bar'}, NotifyServiceName.interaction),
        ({'foo': 'bar'}, NotifyServiceName.export_win),
    ),
)
def test_send_email_notification(context, service_name):
    """
    Test that NotificationClient.send_email_notification method
    works calls through
    to the underlying notify library as expected.
    """
    notify_gateway.send_email_notification(
        'john.smith@example.net',
        'foobar',
        context,
        service_name,
    )
    expected_context = context or {}
    expected_service_name = service_name or DEFAULT_SERVICE_NAME
    notification_api_client = notify_gateway.clients[expected_service_name]
    notification_api_client.send_email_notification.assert_called_with(
        email_address='john.smith@example.net',
        template_id='foobar',
        personalisation=expected_context,
    )


@pytest.mark.parametrize(
    'notification_id,service_name',
    (
        (uuid4(), None),
        (uuid4(), NotifyServiceName.omis),
        (uuid4(), NotifyServiceName.investment),
        (uuid4(), NotifyServiceName.interaction),
        (uuid4(), NotifyServiceName.export_win),
    ),
)
def test_get_notification_by_id(notification_id, service_name):
    """
    Test that NotificationClient.get_notification_by_id method
    works calls through
    to the underlying notify library as expected.
    """
    notify_gateway.get_notification_by_id(
        notification_id,
        service_name,
    )
    expected_service_name = service_name or DEFAULT_SERVICE_NAME
    notification_api_client = notify_gateway.clients[expected_service_name]
    notification_api_client.get_notification_by_id.assert_called_with(notification_id)
