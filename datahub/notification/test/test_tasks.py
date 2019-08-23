import pytest

from datahub.notification import notify_gateway
from datahub.notification.constants import DEFAULT_SERVICE_NAME, NotifyServiceName
from datahub.notification.tasks import send_email_notification


@pytest.mark.django_db
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
